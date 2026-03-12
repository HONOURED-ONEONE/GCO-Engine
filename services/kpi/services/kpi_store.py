import json
import fcntl
import os
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Optional
from services.kpi.db.session import SessionLocal, is_db_enabled
from services.kpi.db.models import KPIEntry
from services.kpi.repositories.kpi_repository import KPIRepository

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
        if is_db_enabled():
            with SessionLocal() as db:
                repo = KPIRepository(db)
                entries = repo.get_all()
                items = [self._to_dict(e) for e in entries]
                return {"items": items}

        with open(self.path, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {"items": []}
            fcntl.flock(f, fcntl.LOCK_UN)
            return data

    def _to_dict(self, e: KPIEntry) -> dict:
        return {
            "batch_id": e.batch_id,
            "energy_kwh": e.energy_kwh,
            "yield_pct": e.yield_pct,
            "quality_deviation": e.quality_deviation,
            "ingested_at": e.ingested_at.isoformat() + "Z",
            "updated_at": e.updated_at.isoformat() + "Z" if e.updated_at else None,
            "anomaly_flag": e.anomaly_flag,
            "anomaly_reasons": e.anomaly_reasons or [],
            "hash": e.hash
        }

    def upsert(self, item: dict) -> tuple:
        if is_db_enabled():
            with SessionLocal() as db:
                repo = KPIRepository(db)
                existing = repo.get_by_batch_id(item["batch_id"])
                now = datetime.utcnow()
                
                if existing:
                    status = "updated"
                    existing.energy_kwh = item["energy_kwh"]
                    existing.yield_pct = item["yield_pct"]
                    existing.quality_deviation = item["quality_deviation"]
                    existing.updated_at = now
                    existing.anomaly_flag = item["anomaly_flag"]
                    existing.anomaly_reasons = item.get("anomaly_reasons", [])
                    existing.hash = _get_hash(
                        existing.batch_id, existing.energy_kwh, 
                        existing.yield_pct, existing.quality_deviation
                    )
                    repo.update(existing)
                else:
                    status = "ingested"
                    entry = KPIEntry(
                        batch_id=item["batch_id"],
                        energy_kwh=item["energy_kwh"],
                        yield_pct=item["yield_pct"],
                        quality_deviation=item["quality_deviation"],
                        ingested_at=now,
                        anomaly_flag=item["anomaly_flag"],
                        anomaly_reasons=item.get("anomaly_reasons", []),
                        hash=_get_hash(
                            item["batch_id"], item["energy_kwh"], 
                            item["yield_pct"], item["quality_deviation"]
                        )
                    )
                    repo.add(entry)
                
                return status, self.load_all()

        with open(self.path, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.seek(0)
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {"items": []}

            items = data.get("items", [])
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
        if is_db_enabled():
            with SessionLocal() as db:
                repo = KPIRepository(db)
                entries = repo.get_recent(limit)
                return [self._to_dict(e) for e in entries]

        data = self.load_all()
        items = data.get("items", [])
        def sort_key(x):
            ts = x.get("updated_at") or x.get("ingested_at")
            return ts or ""
        sorted_items = sorted(items, key=sort_key, reverse=True)
        return sorted_items[:limit]

    def stats_last_n(self, n: int = 10) -> dict:
        if is_db_enabled():
            with SessionLocal() as db:
                repo = KPIRepository(db)
                recent_items = repo.get_last_n_chronological(n)
                
                energy_vals = [i.energy_kwh for i in recent_items]
                yield_vals = [i.yield_pct for i in recent_items]
                
                import numpy as np
                p10_p90_energy = [float(np.percentile(energy_vals, 10)), float(np.percentile(energy_vals, 90))] if energy_vals else [0.0, 0.0]
                p10_p90_yield = [float(np.percentile(yield_vals, 10)), float(np.percentile(yield_vals, 90))] if yield_vals else [0.0, 0.0]
                
                anomaly_count = repo.count_anomalies()
                
                return {
                    "p10_p90": {
                        "energy_kwh": p10_p90_energy,
                        "yield_pct": p10_p90_yield
                    },
                    "anomaly_count": anomaly_count
                }

        data = self.load_all()
        items = data.get("items", [])
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
