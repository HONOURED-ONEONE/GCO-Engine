import os
import time
import httpx
from typing import Dict, Any, Tuple

GOVERNANCE_BASE = os.environ.get("GOVERNANCE_BASE", "http://localhost:8001")
CACHE_TTL = 5.0

class GovernanceClient:
    def __init__(self):
        self._cache = None
        self._cache_time = 0.0
        self.hits = 0
        self.misses = 0

    def get_active_state(self, auth_header: str = None) -> Dict[str, Any]:
        now = time.time()
        if self._cache and (now - self._cache_time) < CACHE_TTL:
            self.hits += 1
            return self._cache

        self.misses += 1
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        else:
            headers["Authorization"] = "Bearer system_01"

        try:
            resp = httpx.get(f"{GOVERNANCE_BASE}/governance/active", headers=headers, timeout=5.0)
            resp.raise_for_status()
            data = resp.json()
            self._cache = data
            self._cache_time = now
            return data
        except Exception as e:
            raise RuntimeError(f"Governance service unavailable: {str(e)}")
            
governance_client = GovernanceClient()
