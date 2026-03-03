from typing import Optional, List, Dict, Any
from app.api.utils.io import read_json, write_json, KPI_STORE_FILE
from app.api.services.corridor import propose_corridor_change

def maybe_propose_update(window_size: int = 3):
    store = read_json(KPI_STORE_FILE)
    kpis = store.get("items", [])
    if len(kpis) < window_size:
        return None

    recent = kpis[-window_size:]
    batch_ids = [k["batch_id"] for k in recent]
    
    avg_energy = sum(k["energy_kwh"] for k in recent) / window_size
    avg_yield = sum(k["yield_pct"] for k in recent) / window_size
    quality_issues = sum(1 for k in recent if k["quality_deviation"])
    
    # Previous window for comparison
    prev_window = kpis[-(window_size*2):-window_size]
    prev_avg_energy = sum(k["energy_kwh"] for k in prev_window) / len(prev_window) if prev_window else avg_energy
    
    energy_delta_pct = ((avg_energy - prev_avg_energy) / prev_avg_energy) * 100 if prev_avg_energy != 0 else 0
    
    delta = {}
    summary = ""
    confidence = 0.5
    metrics = {
        "energy_delta_pct": round(energy_delta_pct, 2),
        "quality_issues": quality_issues,
        "yield_mean": round(avg_yield, 2)
    }

    # Rule 1: Energy improvement (Avg energy down >= 3% and no quality issues)
    if energy_delta_pct <= -3.0 and quality_issues == 0:
        delta = {"temperature_upper": -0.5}
        summary = f"Energy decreased by {abs(energy_delta_pct):.1f}% over last {window_size} batches with stable quality."
        confidence = 0.78
        
    # Rule 2: Quality issues (>=2 in window) -> Widen
    elif quality_issues >= 2:
        delta = {"temperature_upper": 0.5, "temperature_lower": -0.5}
        summary = f"Detected {quality_issues} quality deviations in last {window_size} batches. Proposing wider bounds."
        confidence = 0.85
        
    # Rule 3: Yield low (< 85%) -> Small bump to flow upper
    elif avg_yield < 85.0:
        delta = {"flow_upper": 0.2}
        summary = f"Average yield ({avg_yield:.1f}%) below target. Proposing slight flow upper bound increase."
        confidence = 0.65

    if delta:
        evidence = {
            "summary": summary,
            "kpi_window": batch_ids,
            "metrics": metrics,
            "confidence": confidence
        }
        return propose_corridor_change(delta, evidence)

    return None
