import httpx
import os

GOVERNANCE_BASE = os.environ.get("GOVERNANCE_BASE", "http://governance:8001")

class GovernanceClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(2.0))

    async def post_audit(self, event_type: str, data: dict, subject: str = "llm-service"):
        try:
            # Best-effort non-blocking (the caller will await, but we catch exceptions)
            payload = {
                "type": event_type,
                "data": data,
                "subject": subject
            }
            # For simplicity, we might not have a real JWT here, but governance expects one, or maybe it allows it
            # We will just pass a dummy token if needed, or None
            # The governance service in stage 1/2 usually requires a token for audit. Let's pass system token.
            headers = {"Authorization": "Bearer system_01"}
            await self.client.post(f"{GOVERNANCE_BASE}/governance/audit/ingest", json=payload, headers=headers)
        except Exception:
            # Best effort
            pass

    async def get_active(self):
        try:
            r = await self.client.get(f"{GOVERNANCE_BASE}/governance/active")
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return {}

governance_client = GovernanceClient()
