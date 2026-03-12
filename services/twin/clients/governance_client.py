import os
import httpx
import time
from typing import Dict, Any, Optional

class GovernanceClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("GOVERNANCE_BASE", "http://governance:8001")
        self.client = httpx.AsyncClient(timeout=10.0)

    async def get_active(self) -> Dict[str, Any]:
        """
        Fetch currently active corridors/weights.
        """
        url = f"{self.base_url}/governance/active"
        try:
            resp = await self.client.get(url)
            if resp.status_code == 200:
                return resp.json()
            return {}
        except Exception as e:
            print(f"GovernanceClient get_active error: {e}")
            return {}

    async def post_audit(self, event_type: str, data: Dict[str, Any], subject: str = "twin-service"):
        """
        Post best-effort audit logs.
        """
        url = f"{self.base_url}/governance/audit/ingest"
        payload = {
            "type": event_type,
            "data": data,
            "subject": subject,
            "ts": time.time()
        }
        try:
            await self.client.post(url, json=payload)
        except Exception as e:
            print(f"GovernanceClient audit error: {e}")

governance_client = GovernanceClient()
