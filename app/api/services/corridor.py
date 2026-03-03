from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from app.api.utils.io import read_json, write_json, CORRIDOR_FILE, REGISTRY_FILE, next_version
from app.api.utils.cache import TTLCache
from app.api.utils.audit import add_audit_entry

corridor_cache = TTLCache(ttl_sec=5)

# Safety Limits
DELTA_LIMITS = {
    "temperature": 1.0,
    "flow": 0.5
}

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

def propose_corridor_change(delta: Dict[str, float], evidence: Dict[str, Any]):
    registry = read_json(REGISTRY_FILE)
    if "proposals" not in registry:
        registry["proposals"] = []
    
    prop_id = f"prop-{len(registry['proposals']) + 1:04d}"
    proposal = {
        "id": prop_id,
        "delta": delta,
        "evidence": evidence,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    registry["proposals"].append(proposal)
    write_json(REGISTRY_FILE, registry)
    
    add_audit_entry("proposal_created", {"proposal_id": prop_id, "summary": evidence.get("summary")})
    return prop_id

def approve_proposal(prop_id: str, decision: str, notes: Optional[str] = None):
    registry = read_json(REGISTRY_FILE)
    corridor_data = read_json(CORRIDOR_FILE)
    
    proposal = next((p for p in registry.get("proposals", []) if p["id"] == prop_id), None)
    if not proposal:
        return "Not found", None
    if proposal["status"] != "pending":
        return f"Proposal already {proposal['status']}", None
    
    decided_at = datetime.utcnow().isoformat() + "Z"
    proposal["decided_at"] = decided_at
    proposal["notes"] = notes
    proposal["decided_by"] = "human_operator" # Mock human in loop
    
    if decision == "reject":
        proposal["status"] = "rejected"
        write_json(REGISTRY_FILE, registry)
        add_audit_entry("proposal_rejected", {"proposal_id": prop_id, "notes": notes})
        return "rejected", None
    
    # Approve
    active_v = corridor_data["active_version"]
    new_v = next_version(active_v)
    current_bounds = corridor_data["versions"][active_v]["bounds"]
    
    # Deep copy bounds
    new_bounds = {k: v.copy() for k, v in current_bounds.items()}
    
    # Apply delta and validate
    for key, val in proposal["delta"].items():
        if "_" in key:
            param, bound_type = key.rsplit("_", 1) # temperature_upper
            if param in new_bounds and bound_type in ["lower", "upper"]:
                # Clamping delta limits
                limit = DELTA_LIMITS.get(param, 1.0)
                clamped_val = max(-limit, min(limit, val))
                
                new_val = new_bounds[param][bound_type] + clamped_val
                new_bounds[param][bound_type] = round(new_val, 2)
                
    # Invariant check: lower < upper
    for param, bounds in new_bounds.items():
        if bounds["lower"] >= bounds["upper"]:
             # If it breaks, we just reject the approval (or we could fix it, but let's be safe)
             proposal["status"] = "rejected"
             proposal["notes"] = f"Invariant violation: {param} lower >= upper"
             write_json(REGISTRY_FILE, registry)
             return "rejected_due_to_invariants", None

    # Update corridor.json
    corridor_data["versions"][new_v] = {
        "bounds": new_bounds,
        "created_at": decided_at,
        "evidence": proposal["evidence"]["summary"]
    }
    corridor_data["active_version"] = new_v
    write_json(CORRIDOR_FILE, corridor_data)
    
    # Update registry
    proposal["status"] = "approved"
    registry["active_version"] = new_v
    registry["history"].append({
        "version": new_v,
        "at": decided_at,
        "notes": notes or f"Approved {prop_id}"
    })
    write_json(REGISTRY_FILE, registry)
    
    # Invalidate Cache
    corridor_cache.delete("active")
    
    add_audit_entry("version_commit", {"version": new_v, "proposal_id": prop_id})
    
    return "approved", new_v

def get_pending_proposals():
    registry = read_json(REGISTRY_FILE)
    return [p for p in registry.get("proposals", []) if p["status"] == "pending"]

def get_all_proposals(status: Optional[str] = None):
    registry = read_json(REGISTRY_FILE)
    proposals = registry.get("proposals", [])
    if status:
        proposals = [p for p in proposals if p["status"] == status]
    return proposals

def get_corridor_diff(from_v: str, to_v: str):
    corridor_data = read_json(CORRIDOR_FILE)
    v1 = corridor_data["versions"].get(from_v)
    v2 = corridor_data["versions"].get(to_v)
    
    if not v1 or not v2:
        return None
    
    changes = {}
    params = set(v1["bounds"].keys()) | set(v2["bounds"].keys())
    
    for p in params:
        b1 = v1["bounds"].get(p, {"lower": 0, "upper": 0})
        b2 = v2["bounds"].get(p, {"lower": 0, "upper": 0})
        changes[p] = {
            "lower": {"from": b1["lower"], "to": b2["lower"]},
            "upper": {"from": b1["upper"], "to": b2["upper"]}
        }
        
    # Impact hints (Mocked logic)
    impact_hints = {
        "energy": "likely stable",
        "quality": "likely stable",
        "yield": "likely stable"
    }
    
    # Simple logic for hints
    if any(changes[p]["upper"]["to"] < changes[p]["upper"]["from"] for p in changes if "temperature" in p):
        impact_hints["energy"] = "likely small decrease"
    if any(changes[p]["upper"]["to"] > changes[p]["upper"]["from"] for p in changes if "flow" in p):
        impact_hints["yield"] = "slight increase"
        
    return {
        "from_version": from_v,
        "to_version": to_v,
        "changes": changes,
        "impact_hints": impact_hints
    }
