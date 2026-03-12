import os
import httpx
from typing import Dict, Any, Optional

class OptimizerClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("OPTIMIZER_BASE", "http://optimizer:8002")
        self.client = httpx.AsyncClient(timeout=10.0)

    async def recommend(self, batch_id: str, ts_data: Dict[str, Any], mode: str = "balanced") -> Dict[str, float]:
        """
        Query optimizer for recommended setpoints.
        """
        url = f"{self.base_url}/optimize/recommend"
        payload = {
            "batch_id": batch_id,
            "ts_data": ts_data,
            "mode": mode
        }
        try:
            # Note: For real environment, we'd need auth headers. 
            # Gateway handles this, but service-to-service often uses internal tokens or bypasses OPA if inside network.
            # Assuming for now we pass a system token or it's open internally.
            resp = await self.client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("setpoints", {"temperature": 70.0, "flow": 12.0})
            return {"temperature": 70.0, "flow": 12.0} # Fallback
        except Exception as e:
            print(f"OptimizerClient error: {e}")
            return {"temperature": 70.0, "flow": 12.0} # Fallback

optimizer_client = OptimizerClient()
