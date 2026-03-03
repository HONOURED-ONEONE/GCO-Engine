from datetime import datetime
from typing import Any, Dict
from app.api.utils.io import read_json, write_json, REGISTRY_FILE

def add_audit_entry(event_type: str, data: Dict[str, Any]):
    registry = read_json(REGISTRY_FILE)
    if "audit" not in registry:
        registry["audit"] = []
    
    # Check if audit is a dict (old format) or list
    if isinstance(registry["audit"], dict):
        registry["audit"] = []
        
    entry = {
        "at": datetime.utcnow().isoformat() + "Z",
        "type": event_type,
        "data": data
    }
    registry["audit"].append(entry)
    write_json(REGISTRY_FILE, registry)

def get_audit_entries(limit: int = 100):
    registry = read_json(REGISTRY_FILE)
    audit = registry.get("audit", [])
    if isinstance(audit, dict):
        return []
    return sorted(audit, key=lambda x: x["at"], reverse=True)[:limit]
