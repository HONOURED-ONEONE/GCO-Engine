import httpx
import time
from typing import Dict, Any, Tuple
from .config import OPA_BASE

_cache = {}
CACHE_TTL = 2.0

async def evaluate(client: httpx.AsyncClient, input_data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
    req_data = input_data.get("request", {})
    method = req_data.get("method")
    path = req_data.get("path")
    role = req_data.get("claims", {}).get("role")
    
    cache_key = f"{method}:{path}:{role}"
    now = time.time()
    
    if cache_key in _cache:
        entry = _cache[cache_key]
        if now - entry["ts"] < CACHE_TTL:
            return entry["allow"], entry["headers"]

    try:
        resp = await client.post(
            f"{OPA_BASE}/v1/data/pepgw/authz/opa_output",
            json={"input": input_data}
        )
        resp.raise_for_status()
        result = resp.json().get("result", {})
        allow = result.get("allow", False)
        headers = result.get("headers", {})
        
        _cache[cache_key] = {"allow": allow, "headers": headers, "ts": now}
        return allow, headers
    except Exception:
        return False, {}
