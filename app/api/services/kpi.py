import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.api.utils.io import read_json, write_json, KPI_STORE_FILE
from app.api.utils.audit import add_audit_entry
from app.api.services.marl import maybe_propose_update

def ingest_kpi_service(batch_id: str, energy_kwh: float, yield_pct: float, quality_deviation: bool):
    store = read_json(KPI_STORE_FILE)
    if "items" not in store:
        store["items"] = []
    
    # Anomaly detection
    anomaly_flag = quality_deviation or yield_pct < 80.0
    
    # Simple rolling window for energy anomaly
    recent_kpis = store["items"][-10:]
    if len(recent_kpis) >= 5:
        energies = [k["energy_kwh"] for k in recent_kpis]
        avg_energy = sum(energies) / len(energies)
        # If energy is 20% away from avg, mark as anomaly (simple proxy for p10/p90)
        if abs(energy_kwh - avg_energy) > 0.2 * avg_energy:
            anomaly_flag = True

    # Hash for idempotency/integrity
    data_str = f"{batch_id}|{energy_kwh}|{yield_pct}|{quality_deviation}"
    kpi_hash = hashlib.sha1(data_str.encode()).hexdigest()
    
    new_item = {
        "batch_id": batch_id,
        "energy_kwh": energy_kwh,
        "yield_pct": yield_pct,
        "quality_deviation": quality_deviation,
        "ingested_at": datetime.utcnow().isoformat() + "Z",
        "anomaly_flag": anomaly_flag,
        "hash": kpi_hash
    }
    
    # Upsert logic
    existing_idx = next((i for i, item in enumerate(store["items"]) if item["batch_id"] == batch_id), None)
    
    event_type = "kpi_ingest"
    if existing_idx is not None:
        store["items"][existing_idx] = new_item
        event_type = "kpi_upsert"
    else:
        store["items"].append(new_item)
    
    write_json(KPI_STORE_FILE, store)
    
    add_audit_entry(event_type, {"batch_id": batch_id, "anomaly_flag": anomaly_flag}, "system")
    
    # Trigger MARL
    proposal_id = maybe_propose_update()
    
    return anomaly_flag, event_type == "kpi_upsert", proposal_id

def get_recent_kpis(limit: int = 50):
    store = read_json(KPI_STORE_FILE)
    items = store.get("items", [])
    return sorted(items, key=lambda x: x["ingested_at"], reverse=True)[:limit]
