import os
import requests
from ..utils.metrics import metrics

TWIN_BASE = os.getenv("TWIN_BASE", "http://twin:8007")

def get_counterfactuals(payload: dict):
    try:
        r = requests.post(f"{TWIN_BASE}/twin/counterfactuals", json=payload, timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception:
        metrics["twin_cf_failures"] = metrics.get("twin_cf_failures", 0) + 1
    return {}
