import os
import httpx
from typing import Dict, Any, Optional

GOVERNANCE_BASE = os.environ.get("GOVERNANCE_BASE", "http://governance:8001")
SYSTEM_TOKEN = os.environ.get("GATEWAY_SYSTEM_TOKEN", "system_01")

class GovernanceClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=5.0)

    async def get_active(self) -> Dict[str, Any]:
        try:
            r = await self.client.get(
                f"{GOVERNANCE_BASE}/governance/active",
                headers={"Authorization": f"Bearer {SYSTEM_TOKEN}"}
            )
            if r.status_code == 200:
                return r.json()
            return {}
        except Exception:
            return {}

    async def post_audit(self, event_type: str, data: Dict[str, Any], subject: str):
        try:
            payload = {
                "type": event_type,
                "data": data,
                "subject": subject
            }
            await self.client.post(
                f"{GOVERNANCE_BASE}/governance/audit/ingest",
                json=payload,
                headers={"Authorization": f"Bearer {SYSTEM_TOKEN}"}
            )
        except Exception:
            # Audit failure should not block the main operation but should be recorded in health
            pass

governance_client = GovernanceClient()
