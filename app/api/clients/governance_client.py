import os
import requests
from typing import Dict, Any, Tuple, List, Optional
from app.api.services.corridor import get_active_corridor, get_all_proposals, propose_corridor_change, approve_proposal
from app.api.services.mode import get_current_mode_data
from app.api.utils.audit import add_audit_entry

class GovernanceClient:
    """
    Compatibility client for accessing the Governance Control Plane.
    If GOVERNANCE_BASE is set, it makes HTTP requests to the governance microservice.
    Otherwise, it accesses the local JSON state directly (monolith behavior).
    """
    def __init__(self, token: str = "system"):
        self.base_url = os.environ.get("GOVERNANCE_BASE", "").rstrip("/")
        self.token = token
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def get_active(self) -> Tuple[str, Dict[str, Any], str, Dict[str, float]]:
        if self.base_url:
            resp = requests.get(f"{self.base_url}/governance/active", headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
            return data["active_version"], data["bounds"], data["last_mode"], data["last_mode_weights"]
        else:
            # Fallback to local
            v, bounds_data = get_active_corridor()
            mode_data = get_current_mode_data()
            return v, bounds_data["bounds"], mode_data["mode"], mode_data["weights"]

    def list_proposals(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.base_url:
            params = {"status": status} if status else {}
            resp = requests.get(f"{self.base_url}/corridor/proposals", params=params, headers=self.headers)
            resp.raise_for_status()
            return resp.json()["items"]
        else:
            return get_all_proposals(status)

    def propose(self, delta: Dict[str, float], evidence: Dict[str, Any]) -> str:
        if self.base_url:
            payload = {"delta": delta, "evidence": evidence}
            resp = requests.post(f"{self.base_url}/corridor/propose", json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json()["proposal_id"]
        else:
            return propose_corridor_change(delta, evidence)

    def approve(self, proposal_id: str, decision: str, notes: Optional[str] = None) -> Tuple[str, Optional[str]]:
        if self.base_url:
            payload = {"proposal_id": proposal_id, "decision": decision, "notes": notes}
            resp = requests.post(f"{self.base_url}/corridor/approve", json=payload, headers=self.headers)
            resp.raise_for_status()
            data = resp.json()
            return data["status"], data.get("new_version")
        else:
            # Note: local approve_proposal signature returns (status, new_version)
            return approve_proposal(proposal_id, decision, notes, self.token)

    def audit_ingest(self, event_type: str, data: Dict[str, Any]) -> Optional[str]:
        if self.base_url:
            payload = {"event_type": event_type, "data": data, "user_id": self.token}
            resp = requests.post(f"{self.base_url}/governance/audit/ingest", json=payload, headers=self.headers)
            resp.raise_for_status()
            return resp.json().get("hash")
        else:
            add_audit_entry(event_type, data, self.token)
            return None # local doesn't return hash directly easily without re-reading
