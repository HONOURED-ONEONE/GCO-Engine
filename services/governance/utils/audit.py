from datetime import datetime
from typing import Any, Dict, List, Optional
import hashlib
import json
from services.governance.utils.io import read_json, write_json, REGISTRY_FILE

def calculate_hash(prev_hash: str, entry_data: Dict[str, Any]) -> str:
    content = f"{prev_hash}|{json.dumps(entry_data, sort_keys=True, separators=(',', ':'))}"
    return hashlib.sha256(content.encode()).hexdigest()

def add_audit_entry(event_type: str, data: Dict[str, Any], user_id: str = "system"):
    registry = read_json(REGISTRY_FILE)
    if "audit" not in registry:
        registry["audit"] = []
    
    if isinstance(registry["audit"], dict):
        registry["audit"] = []
        
    prev_hash = registry["audit"][-1].get("hash", "0"*64) if registry["audit"] else "0"*64
    
    entry_core = {
        "at": datetime.utcnow().isoformat() + "Z",
        "type": event_type,
        "data": data,
        "user_id": user_id
    }
    
    entry_hash = calculate_hash(prev_hash, entry_core)
    entry_core["hash"] = entry_hash
    
    registry["audit"].append(entry_core)
    write_json(REGISTRY_FILE, registry)

def verify_audit_chain() -> tuple[bool, str, int]:
    registry = read_json(REGISTRY_FILE)
    audit = registry.get("audit", [])
    if not audit:
        return True, "0"*64, 0
    
    prev_hash = "0"*64
    for entry in audit:
        entry_copy = entry.copy()
        actual_hash = entry_copy.pop("hash", None)
        if actual_hash is None:
            return False, prev_hash, len(audit)
        expected_hash = calculate_hash(prev_hash, entry_copy)
        if actual_hash != expected_hash:
            return False, actual_hash, len(audit)
        prev_hash = actual_hash
    return True, prev_hash, len(audit)

def get_audit_entries(limit: int = 100):
    registry = read_json(REGISTRY_FILE)
    audit = registry.get("audit", [])
    if isinstance(audit, dict):
        return []
    return sorted(audit, key=lambda x: x["at"], reverse=True)[:limit]
