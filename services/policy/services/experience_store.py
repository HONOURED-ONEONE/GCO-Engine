import json
import os
from filelock import FileLock
from datetime import datetime
from ..utils.metrics import metrics

STORE_FILE = "data/experience_store.json"
LOCK_FILE = "data/experience_store.lock"

def _load_store():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(STORE_FILE):
        return {"by_key": {}, "meta": {"last_update": ""}}
    with open(STORE_FILE, "r") as f:
        try:
            data = json.load(f)
            if "by_key" not in data:
                data["by_key"] = {}
            if "meta" not in data:
                data["meta"] = {"last_update": ""}
            return data
        except Exception:
            return {"by_key": {}, "meta": {"last_update": ""}}

def _save_store(data):
    with open(STORE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_window(key: str, items: list, weights_at_time: dict, decay_map: dict):
    with FileLock(LOCK_FILE):
        store = _load_store()
        if key not in store["by_key"]:
            store["by_key"][key] = []
        
        for item in items:
            it = item.dict() if hasattr(item, "dict") else item
            it["weights_at_time"] = weights_at_time
            # compute features
            it["features"] = {
                "trend_energy": 0.0,
                "trend_yield": 0.0,
                "anomaly": 1 if it.get("quality_deviation") else 0
            }
            store["by_key"][key].append(it)
        
        # Keep bounded length
        store["by_key"][key] = store["by_key"][key][-100:]
        store["meta"]["last_update"] = datetime.utcnow().isoformat()
        
        _save_store(store)
        metrics["store_sizes"] = sum(len(v) for v in store["by_key"].values())

def get_experiences(key: str, limit: int = 100):
    store = _load_store()
    return store.get("by_key", {}).get(key, [])[-limit:]

def compute_uncertainty(key: str) -> float:
    from .uncertainty import rolling_variance, anomaly_density, combine
    items = get_experiences(key)
    if not items:
        return 1.0
    energies = [i["energy_kwh"] for i in items]
    yields = [i["yield_pct"] for i in items]
    
    var_norm = (rolling_variance(energies) / 100.0) + (rolling_variance(yields) / 100.0)
    density = anomaly_density(items)
    n_eff = len(items)
    
    return combine(var_norm, density, n_eff)

def compute_restraint(key: str) -> bool:
    unc = compute_uncertainty(key)
    items = get_experiences(key, limit=5)
    density = sum(1 for i in items if i.get("quality_deviation")) / max(1, len(items))
    return unc > 0.6 or density > 0.25 or sum(1 for i in items if i.get("quality_deviation")) >= 2

def summarize_window(key: str, n: int):
    items = get_experiences(key, limit=n)
    if not items:
        return {"n": 0}
    energies = [i["energy_kwh"] for i in items]
    yields = [i["yield_pct"] for i in items]
    quals = [1 for i in items if i.get("quality_deviation")]
    
    return {
        "n": len(items),
        "energy_mean": sum(energies)/len(energies) if energies else 0,
        "energy_trend": (energies[-1]-energies[0])/max(1, energies[0]) if len(energies)>1 else 0,
        "yield_mean": sum(yields)/len(yields) if yields else 0,
        "yield_trend": (yields[-1]-yields[0])/max(1, yields[0]) if len(yields)>1 else 0,
        "quality_violations": len(quals)
    }
