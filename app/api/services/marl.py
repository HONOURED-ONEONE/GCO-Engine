from typing import Optional, List, Dict, Any
import os
import time
import hashlib
from app.api.utils.io import read_json, write_json, KPI_STORE_FILE, BASE_DATA_DIR
from app.api.services.corridor import propose_corridor_change

POLICY_REGISTRY_FILE = os.path.join(BASE_DATA_DIR, "policy_registry.json")
EXPERIENCE_STORE_FILE = os.path.join(BASE_DATA_DIR, "experience_store.json")

def init_marl_files():
    if not os.path.exists(POLICY_REGISTRY_FILE):
        write_json(POLICY_REGISTRY_FILE, {
            "active_policy_id": "p-001",
            "policies": [
                {
                    "id": "p-001",
                    "hash": "abc12345",
                    "created_at": time.time(),
                    "metrics": {"energy_improvement_pct": 0, "quality_deviation_pct": 0},
                    "description": "Baseline Heuristic Policy"
                }
            ]
        })
    if not os.path.exists(EXPERIENCE_STORE_FILE):
        write_json(EXPERIENCE_STORE_FILE, {"trajectories": []})

def get_active_policy():
    init_marl_files()
    registry = read_json(POLICY_REGISTRY_FILE)
    active_id = registry.get("active_policy_id")
    for p in registry.get("policies", []):
        if p["id"] == active_id:
            return p
    return registry["policies"][0]

def log_experience(batch_id: str, trajectory: List[Dict[str, Any]], reward: float):
    init_marl_files()
    store = read_json(EXPERIENCE_STORE_FILE)
    store["trajectories"].append({
        "batch_id": batch_id,
        "ts": time.time(),
        "trajectory": trajectory,
        "reward": reward,
        "policy_id": get_active_policy()["id"]
    })
    # Keep store manageable for MVP
    if len(store["trajectories"]) > 100:
        store["trajectories"] = store["trajectories"][-100:]
    write_json(EXPERIENCE_STORE_FILE, store)

def train_offline_batch():
    """Simulates offline training from experience store."""
    store = read_json(EXPERIENCE_STORE_FILE)
    trajectories = store.get("trajectories", [])
    if len(trajectories) < 5:
        return None, "Insufficient data for training"
    
    # Simulate policy improvement
    new_id = f"p-{len(read_json(POLICY_REGISTRY_FILE)['policies']) + 1:03d}"
    new_policy = {
        "id": new_id,
        "hash": hashlib.md5(str(time.time()).encode()).hexdigest()[:8],
        "created_at": time.time(),
        "metrics": {"energy_improvement_pct": 3.2, "quality_deviation_pct": 0.1},
        "description": f"Offline trained from {len(trajectories)} trajectories"
    }
    
    registry = read_json(POLICY_REGISTRY_FILE)
    registry["policies"].append(new_policy)
    write_json(POLICY_REGISTRY_FILE, registry)
    return new_policy, None

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

    # Use Active Policy Info for Rationale
    policy = get_active_policy()

    if energy_delta_pct <= -3.0 and quality_issues == 0:
        delta = {"temperature_upper": -0.5}
        summary = f"[{policy['id']}] Energy decreased by {abs(energy_delta_pct):.1f}% with stable quality."
        confidence = 0.78
        
    elif quality_issues >= 2:
        delta = {"temperature_upper": 0.5, "temperature_lower": -0.5}
        summary = f"[{policy['id']}] Detected {quality_issues} quality deviations. Proposing wider bounds."
        confidence = 0.85
        
    elif avg_yield < 85.0:
        delta = {"flow_upper": 0.2}
        summary = f"[{policy['id']}] Yield low. Proposing slight flow upper bound increase."
        confidence = 0.65

    if delta:
        evidence = {
            "summary": summary,
            "kpi_window": batch_ids,
            "metrics": metrics,
            "confidence": confidence,
            "policy_id": policy["id"]
        }
        return propose_corridor_change(delta, evidence)

    return None
