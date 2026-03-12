import os
import requests

KPI_BASE = os.getenv("KPI_BASE", "http://kpi:8005")

def get_recent_kpis(limit=5):
    try:
        r = requests.get(f"{KPI_BASE}/kpi/recent", params={"limit": limit}, timeout=2)
        if r.status_code == 200:
            return r.json().get("items", [])
    except Exception:
        pass
    return []
