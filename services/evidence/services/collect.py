import os
import uuid
import json
import datetime
import httpx
from typing import Optional, Dict, Any, List
from ..utils.metrics import metrics

GOVERNANCE_BASE = os.getenv("GOVERNANCE_BASE", "http://governance:8001")
KPI_BASE = os.getenv("KPI_BASE", "http://kpi:8005")
OPTIMIZER_BASE = os.getenv("OPTIMIZER_BASE", "http://optimizer:8002")
POLICY_BASE = os.getenv("POLICY_BASE", "http://policy:8006")
TWIN_BASE = os.getenv("TWIN_BASE", "http://twin:8007")
LLM_BASE = os.getenv("LLM_BASE", "http://llm:8004")
EVIDENCE_DIR = os.getenv("EVIDENCE_DIR", "./evidence")

TIMEOUT = 2.0

class EvidenceCollector:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        
    async def get_json(self, url: str, default: Any = None) -> Any:
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            metrics.record_downstream_failure()
            return default

    async def post_json(self, url: str, json_data: dict, default: Any = None) -> Any:
        try:
            resp = await self.client.post(url, json=json_data)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            metrics.record_downstream_failure()
            return default

    async def post_audit(self, event_type: str, data: dict, subject: str, run_id: str, request_id: Optional[str] = None):
        url = f"{GOVERNANCE_BASE}/governance/audit"
        audit_payload = {
            "event_type": event_type,
            "data": {**data, "run_id": run_id, "x_request_id": request_id},
            "subject": subject
        }
        try:
            resp = await self.client.post(url, json=audit_payload)
            resp.raise_for_status()
        except Exception:
            metrics.record_audit_failure()

    async def gather_snapshot(self, include_llm: bool, include_twin: bool, rec_limit: int) -> dict:
        run_id = str(uuid.uuid4())
        collected_at = datetime.datetime.utcnow().isoformat() + "Z"
        
        active_ver = await self.get_json(f"{GOVERNANCE_BASE}/governance/corridor/active", default={})
        proposals = await self.get_json(f"{GOVERNANCE_BASE}/governance/proposals", default=[])
        kpis = await self.get_json(f"{KPI_BASE}/kpi/recent?limit={rec_limit}", default=[])
        opt_health = await self.get_json(f"{OPTIMIZER_BASE}/optimizer/health", default={"status": "unknown"})
        
        # Best effort policy active
        policy_active = await self.get_json(f"{POLICY_BASE}/policy/active", default={})
        
        snapshot = {
            "active_version": active_ver.get("version", "unknown"),
            "bounds": active_ver.get("bounds", {}),
            "mode": active_ver.get("mode", "unknown"),
            "weights": active_ver.get("weights", {}),
            "proposals": proposals,
            "recent_kpis": kpis,
            "recent_recommendations": [],
            "policy": policy_active,
            "optimizer_health": opt_health,
            "twin": None,
            "llm": None,
            "collected_at": collected_at,
            "run_id": run_id
        }
        
        if include_twin:
            snapshot["twin"] = await self.get_json(f"{TWIN_BASE}/twin/snapshot", default={})
            
        if include_llm:
            snapshot["llm"] = await self.post_json(f"{LLM_BASE}/llm/summary", {"snapshot": "minimal"}, default={})
            
        return snapshot
        
    def save_snapshot(self, run_id: str, snapshot: dict) -> str:
        run_dir = os.path.join(EVIDENCE_DIR, run_id)
        os.makedirs(run_dir, exist_ok=True)
        path = os.path.join(run_dir, "snapshot.json")
        with open(path, "w") as f:
            json.dump(snapshot, f, indent=2)
        return path
        
    def load_snapshot(self, run_id: str) -> dict:
        path = os.path.join(EVIDENCE_DIR, run_id, "snapshot.json")
        if not os.path.exists(path):
            return {}
        with open(path, "r") as f:
            return json.load(f)

collector = EvidenceCollector()
