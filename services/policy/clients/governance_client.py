import os
import requests
from ..utils.metrics import metrics

GOVERNANCE_BASE = os.getenv("GOVERNANCE_BASE", "http://governance:8001")

def get_active_governance():
    try:
        r = requests.get(f"{GOVERNANCE_BASE}/governance/active", timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"weights": {"energy": 0.33, "quality": 0.34, "yield": 0.33}, "mode": "efficiency_first"}

def list_proposals(status="approved|rejected|pending", limit=50):
    try:
        r = requests.get(f"{GOVERNANCE_BASE}/corridor/proposals", params={"status": status, "limit": limit}, timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []

def propose_corridor(payload: dict):
    try:
        r = requests.post(f"{GOVERNANCE_BASE}/corridor/propose", json=payload, timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}

def post_audit(event_type: str, data: dict, subject: str):
    try:
        requests.post(f"{GOVERNANCE_BASE}/governance/audit", json={
            "event_type": event_type,
            "data": data,
            "subject": subject
        }, timeout=2)
    except Exception:
        metrics["governance_post_failures"] = metrics.get("governance_post_failures", 0) + 1
