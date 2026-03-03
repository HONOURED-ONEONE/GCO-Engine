import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from app.api.utils.io import read_json, write_json, REGISTRY_FILE

from app.api.utils.cache import TTLCache

logger = logging.getLogger(__name__)

mode_cache = TTLCache(ttl_sec=5)

ALLOWED_MODES = {
    "sustainability_first": {
        "id": "sustainability_first",
        "label": "Sustainability-First",
        "weights": {"energy": 0.60, "quality": 0.25, "yield": 0.15},
        "description": "Minimize energy and CO₂ under quality guardrails."
    },
    "production_first": {
        "id": "production_first",
        "label": "Production-First",
        "weights": {"energy": 0.25, "quality": 0.35, "yield": 0.40},
        "description": "Maximize yield/quality within an energy budget."
    }
}

def get_policy() -> List[Dict[str, Any]]:
    return list(ALLOWED_MODES.values())

def get_current_mode_data() -> Dict[str, Any]:
    cached = mode_cache.get("current")
    if cached:
        return cached

    registry = read_json(REGISTRY_FILE)
    
    # Check if keys exist, if not, initialize with defaults
    if "last_mode" not in registry or "last_mode_weights" not in registry:
        logger.warning("version_registry.json missing mode keys, re-initializing.")
        registry["last_mode"] = "sustainability_first"
        registry["last_mode_weights"] = ALLOWED_MODES["sustainability_first"]["weights"]
        registry["last_mode_changed_at"] = datetime.now(timezone.utc).isoformat()
        if "audit" not in registry:
            registry["audit"] = {"mode_changes": []}
        write_json(REGISTRY_FILE, registry)
        
    res = {
        "mode": registry.get("last_mode"),
        "weights": registry.get("last_mode_weights"),
        "changed_at": registry.get("last_mode_changed_at"),
        "operator_id": registry.get("last_operator_id", "stubbed-operator")
    }
    mode_cache.set("current", res)
    return res

def set_mode(mode_id: str, operator_id: str = "stubbed-operator") -> Tuple[Dict[str, Any], bool]:
    if mode_id not in ALLOWED_MODES:
        raise ValueError(f"Invalid mode: {mode_id}. Allowed: {list(ALLOWED_MODES.keys())}")
    
    registry = read_json(REGISTRY_FILE)
    current_mode = registry.get("last_mode")
    
    new_mode_data = ALLOWED_MODES[mode_id]
    weights = new_mode_data["weights"]
    now = datetime.now(timezone.utc).isoformat()
    
    changed = False
    if current_mode != mode_id:
        logger.info(f"Mode changing from {current_mode} to {mode_id}")
        
        # Build audit entry
        audit_entry = {
            "at": now,
            "operator": operator_id,
            "from": current_mode,
            "to": mode_id,
            "weights": weights
        }
        
        registry["last_mode"] = mode_id
        registry["last_mode_weights"] = weights
        registry["last_mode_changed_at"] = now
        registry["last_operator_id"] = operator_id
        
        if "audit" not in registry:
            registry["audit"] = {"mode_changes": []}
        registry["audit"]["mode_changes"].append(audit_entry)
        
        write_json(REGISTRY_FILE, registry)
        changed = True
        message = "Applied"
        # Invalidate cache
        mode_cache.cache = {}
    else:
        logger.info(f"Mode already set to {mode_id}. No change.")
        message = "No change"
        now = registry.get("last_mode_changed_at", now)

    response_data = {
        "mode": mode_id,
        "weights": weights,
        "changed": changed,
        "changed_at": now,
        "message": message
    }
    
    return response_data, changed
