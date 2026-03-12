import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
from services.governance.utils.io import read_json, write_json, REGISTRY_FILE
from services.governance.utils.cache import TTLCache
from services.governance.db.session import SessionLocal, is_db_enabled
from services.governance.db.models import ModeState
from services.governance.repositories.mode_repository import ModeRepository
from services.governance.utils.audit import add_audit_entry

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

    if is_db_enabled():
        with SessionLocal() as db:
            repo = ModeRepository(db)
            current = repo.get_current()
            if current:
                res = {
                    "mode": current.mode,
                    "weights": current.weights,
                    "changed_at": current.changed_at.isoformat() + "Z",
                    "operator_id": current.operator_id
                }
                mode_cache.set("current", res)
                return res

    registry = read_json(REGISTRY_FILE)
    if "last_mode" not in registry or "last_mode_weights" not in registry:
        logger.warning("version_registry.json missing mode keys, re-initializing.")
        registry["last_mode"] = "sustainability_first"
        registry["last_mode_weights"] = ALLOWED_MODES["sustainability_first"]["weights"]
        registry["last_mode_changed_at"] = datetime.now(timezone.utc).isoformat()
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
    
    current_mode_data = get_current_mode_data()
    current_mode = current_mode_data.get("mode")
    
    new_mode_data = ALLOWED_MODES[mode_id]
    weights = new_mode_data["weights"]
    now_dt = datetime.now(timezone.utc)
    now = now_dt.isoformat() + "Z"
    
    changed = False
    if current_mode != mode_id:
        logger.info(f"Mode changing from {current_mode} to {mode_id}")
        
        if is_db_enabled():
            with SessionLocal() as db:
                repo = ModeRepository(db)
                ms = ModeState(
                    mode=mode_id,
                    weights=weights,
                    changed_at=now_dt,
                    operator_id=operator_id
                )
                repo.add(ms)
        else:
            registry = read_json(REGISTRY_FILE)
            registry["last_mode"] = mode_id
            registry["last_mode_weights"] = weights
            registry["last_mode_changed_at"] = now
            registry["last_operator_id"] = operator_id
            write_json(REGISTRY_FILE, registry)
        
        add_audit_entry("mode_change", {
            "from": current_mode,
            "to": mode_id,
            "weights": weights
        }, operator_id)
        
        changed = True
        message = "Applied"
        mode_cache.cache = {}
    else:
        logger.info(f"Mode already set to {mode_id}. No change.")
        message = "No change"
        now = current_mode_data.get("changed_at", now)

    response_data = {
        "mode": mode_id,
        "weights": weights,
        "changed": changed,
        "changed_at": now,
        "message": message
    }
    
    return response_data, changed
