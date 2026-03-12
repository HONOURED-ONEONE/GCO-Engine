import httpx
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

POLICY_NOTIFY_BASE = os.getenv("POLICY_NOTIFY_BASE", "")

async def maybe_notify(window_summary: Dict[str, Any], headers: Dict[str, str]) -> None:
    if not POLICY_NOTIFY_BASE:
        return

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{POLICY_NOTIFY_BASE}/policy/maybe-propose",
                json=window_summary,
                headers=headers,
                timeout=2.0
            )
    except Exception as e:
        logger.warning(f"Failed to notify policy service: {e}")
