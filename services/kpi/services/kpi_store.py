import json
import fcntl
import os
import hashlib
from datetime import datetime, timezone

STORE_PATH = os.getenv("KPI_STORE_PATH", "./data/kpi_store.json")

def _get_hash(batch_id, energy, yield_pct, quality):
    raw = f"{batch_id}|{energy}|{yield_pct}|{quality}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()

class KPIStore:
    def __init__(self, path=STORE_PATH):
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, "w") as f:
                json.dump({"items": []}, f)

    def load_all(self) -> dict:
        with open(self.path, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {"items": []}
            fcntl.flock(f, fcntl.LOCK_UN)
            return data

    def upsert(self, item: dict) -> tuple:
        with open(self.path, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.seek(0)
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {"items": []}

            items = data.get("items", [])
            
            # Find if exists
            existing_idx = -1
            for i, existing in enumerate(items):
                if existing["batch_id"] == item["batch_id"]:
                    existing_idx = i
                    break
            
            status = "ingested"
            now_iso = datetime.now(timezone.utc).isoformat()
            
            if existing_idx >= 0:
                status = "updated"
                existing = items[existing_idx]
                existing["energy_kwh"] = item["energy_kwh"]
                existing["yield_pct"] = item["yield_pct"]
                existing["quality_deviation"] = item["quality_deviation"]
                existing["updated_at"] = now_iso
                existing["anomaly_flag"] = item["anomaly_flag"]
                existing["anomaly_reasons"] = item.get("anomaly_reasons", [])
                existing["hash"] = _get_hash(
                    existing["batch_id"], existing["energy_kwh"], 
                    existing["yield_pct"], existing["quality_deviation"]
                )
            else:
                item["ingested_at"] = now_iso
                item["updated_at"] = None
                item["hash"] = _get_hash(
                    item["batch_id"], item["energy_kwh"], 
                    item["yield_pct"], item["quality_deviation"]
                )
                items.append(item)
            
            data["items"] = items
            
            f.seek(0)
            f.truncate()
            json.dump(data, f)
            f.flush()
            fcntl.flock(f, fcntl.LOCK_UN)
            
            return status, data

    def recent(self, limit: int) -> list:
        data = self.load_all()
        items = data.get("items", [])
        
        # Sort by updated_at if exists else ingested_at
        def sort_key(x):
            ts = x.get("updated_at") or x.get("ingested_at")
            return ts or ""
            
        sorted_items = sorted(items, key=sort_key, reverse=True)
        return sorted_items[:limit]

    def stats_last_n(self, n: int = 10) -> dict:
        data = self.load_all()
        items = data.get("items", [])
        
        # We need the chronological order to get the last N batches
        def sort_key(x):
            ts = x.get("updated_at") or x.get("ingested_at")
            return ts or ""
            
        sorted_items = sorted(items, key=sort_key)
        recent_items = sorted_items[-n:] if n > 0 else sorted_items
        
        energy_vals = [i["energy_kwh"] for i in recent_items if "energy_kwh" in i]
        yield_vals = [i["yield_pct"] for i in recent_items if "yield_pct" in i]
        
        import numpy as np
        p10_p90_energy = [float(np.percentile(energy_vals, 10)), float(np.percentile(energy_vals, 90))] if energy_vals else [0.0, 0.0]
        p10_p90_yield = [float(np.percentile(yield_vals, 10)), float(np.percentile(yield_vals, 90))] if yield_vals else [0.0, 0.0]
        
        anomaly_count = sum(1 for i in items if i.get("anomaly_flag"))
        
        return {
            "p10_p90": {
                "energy_kwh": p10_p90_energy,
                "yield_pct": p10_p90_yield
            },
            "anomaly_count": anomaly_count
        }

kpi_store = KPIStore()
