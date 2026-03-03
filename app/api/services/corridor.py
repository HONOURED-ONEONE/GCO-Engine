from datetime import datetime
from typing import Dict, Any, Optional
from app.api.utils.io import read_json, write_json, CORRIDOR_FILE, REGISTRY_FILE
from app.api.utils.versioning import next_version
from app.api.utils.cache import TTLCache

corridor_cache = TTLCache(ttl_sec=5)

def get_active_corridor():
    cached = corridor_cache.get("active")
    if cached:
        return cached
    
    corridor_data = read_json(CORRIDOR_FILE)
    active_v = corridor_data.get("active_version", "v1")
    res = active_v, corridor_data["versions"][active_v]
    corridor_cache.set("active", res)
    return res

def get_version_history():
    registry = read_json(REGISTRY_FILE)
    return registry.get("history", [])

def propose_corridor_change(delta: Dict[str, float], evidence: str):
    registry = read_json(REGISTRY_FILE)
    prop_id = f"prop-{len(registry.get('proposals', [])) + 1:04d}"
    proposal = {
        "id": prop_id,
        "delta": delta,
        "evidence": evidence,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    if "proposals" not in registry:
        registry["proposals"] = []
    registry["proposals"].append(proposal)
    write_json(REGISTRY_FILE, registry)
    return prop_id

def approve_proposal(prop_id: str, decision: str, notes: Optional[str] = None):
    registry = read_json(REGISTRY_FILE)
    corridor_data = read_json(CORRIDOR_FILE)
    
    proposal = next((p for p in registry.get("proposals", []) if p["id"] == prop_id), None)
    if not proposal or proposal["status"] != "pending":
        return "Not found or not pending", None
    
    if decision == "reject":
        proposal["status"] = "rejected"
        proposal["notes"] = notes
        write_json(REGISTRY_FILE, registry)
        return "rejected", None
    
    # Approve
    active_v = corridor_data["active_version"]
    new_v = next_version(active_v)
    current_bounds = corridor_data["versions"][active_v]["bounds"]
    
    # Deep copy bounds
    new_bounds = {k: v.copy() for k, v in current_bounds.items()}
    
    # Apply delta
    for key, val in proposal["delta"].items():
        if "_" in key:
            param, bound_type = key.rsplit("_", 1) # temperature_upper
            if param in new_bounds and bound_type in ["lower", "upper"]:
                new_bounds[param][bound_type] += val
    
    # Update corridor.json
    corridor_data["versions"][new_v] = {
        "bounds": new_bounds,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "evidence": proposal["evidence"]
    }
    corridor_data["active_version"] = new_v
    write_json(CORRIDOR_FILE, corridor_data)
    
    # Update registry
    proposal["status"] = "approved"
    proposal["notes"] = notes
    registry["active_version"] = new_v
    registry["history"].append({
        "version": new_v,
        "at": datetime.utcnow().isoformat() + "Z",
        "notes": notes or f"Approved {prop_id}"
    })
    write_json(REGISTRY_FILE, registry)
    
    return "approved", new_v

def get_pending_proposals():
    registry = read_json(REGISTRY_FILE)
    return [p for p in registry.get("proposals", []) if p["status"] == "pending"]
