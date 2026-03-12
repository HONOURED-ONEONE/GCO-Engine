import httpx
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

GOVERNANCE_BASE = os.getenv("GOVERNANCE_BASE", "http://governance:8001")

async def post_audit(event_type: str, data: Dict[str, Any], subject: str, request_id: str = "") -> None:
    payload = {
        "type": event_type,
        "data": data,
        "x_request_id": request_id,
        "by": subject
    }
    
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{GOVERNANCE_BASE}/governance/audit/ingest",
                json=payload,
                timeout=2.0
            )
    except Exception as e:
        logger.warning(f"Failed to post governance audit: {e}")
