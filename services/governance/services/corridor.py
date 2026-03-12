from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from services.governance.utils.io import read_json, write_json, CORRIDOR_FILE, REGISTRY_FILE, next_version
from services.governance.utils.cache import TTLCache
from services.governance.utils.audit import add_audit_entry
from services.governance.db.session import SessionLocal, is_db_enabled
from services.governance.db.models import CorridorVersion, Proposal as DBProposal
from services.governance.repositories.corridor_repository import CorridorRepository
from services.governance.repositories.proposal_repository import ProposalRepository

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
    
    if is_db_enabled():
        with SessionLocal() as db:
            repo = CorridorRepository(db)
            active = repo.get_active()
            if active:
                res = active.version_tag, active.bounds
                corridor_cache.set("active", res)
                return res
    
    # Fallback or file-backed
    corridor_data = read_json(CORRIDOR_FILE)
    active_v = corridor_data.get("active_version", "v1")
    res = active_v, corridor_data["versions"][active_v]
    corridor_cache.set("active", res)
    return res

def get_version_history():
    if is_db_enabled():
        with SessionLocal() as db:
            repo = CorridorRepository(db)
            versions = repo.get_all()
            return [{"version": v.version_tag, "at": v.created_at.isoformat() + "Z", "notes": v.evidence} for v in versions]
            
    registry = read_json(REGISTRY_FILE)
    return registry.get("history", [])

def propose_corridor_change(delta: Dict[str, float], evidence: Dict[str, Any], user_id: str = "system"):
    if is_db_enabled():
        with SessionLocal() as db:
            repo = ProposalRepository(db)
            count = repo.count()
            prop_id = f"prop-{count + 1:04d}"
            proposal = DBProposal(
                proposal_id=prop_id,
                delta=delta,
                evidence=evidence,
                status="pending",
                created_at=datetime.utcnow(),
                created_by=user_id
            )
            repo.add(proposal)
            add_audit_entry("proposal_created", {"proposal_id": prop_id, "summary": evidence.get("summary")}, user_id)
            return prop_id

    # File-backed
    registry = read_json(REGISTRY_FILE)
    if "proposals" not in registry:
        registry["proposals"] = []
    
    prop_id = f"prop-{len(registry['proposals']) + 1:04d}"
    proposal = {
        "id": prop_id,
        "delta": delta,
        "evidence": evidence,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "created_by": user_id
    }
    registry["proposals"].append(proposal)
    write_json(REGISTRY_FILE, registry)
    
    add_audit_entry("proposal_created", {"proposal_id": prop_id, "summary": evidence.get("summary")}, user_id)
    return prop_id

def approve_proposal(prop_id: str, decision: str, notes: Optional[str] = None, user_id: str = "system"):
    if is_db_enabled():
        with SessionLocal() as db:
            prop_repo = ProposalRepository(db)
            corr_repo = CorridorRepository(db)
            proposal = prop_repo.get_by_id(prop_id)
            if not proposal:
                return "Not found", None
            if proposal.status != "pending":
                return f"Proposal already {proposal.status}", None
            
            decided_at = datetime.utcnow()
            proposal.decided_at = decided_at
            proposal.notes = notes
            proposal.decided_by = user_id
            
            if decision == "reject":
                proposal.status = "rejected"
                prop_repo.update(proposal)
                add_audit_entry("proposal_rejected", {"proposal_id": prop_id, "notes": notes}, user_id)
                return "rejected", None
            
            # Approve
            active_cv = corr_repo.get_active()
            active_v = active_cv.version_tag if active_cv else "v1"
            new_v = next_version(active_v)
            current_bounds = active_cv.bounds if active_cv else {}
            
            new_bounds = {k: v.copy() for k, v in current_bounds.items()}
            for key, val in proposal.delta.items():
                if "_" in key:
                    param, bound_type = key.rsplit("_", 1)
                    if param in new_bounds and bound_type in ["lower", "upper"]:
                        limit = DELTA_LIMITS.get(param, 1.0)
                        clamped_val = max(-limit, min(limit, val))
                        new_val = new_bounds[param][bound_type] + clamped_val
                        new_bounds[param][bound_type] = round(new_val, 2)
            
            for param, bounds in new_bounds.items():
                if bounds["lower"] >= bounds["upper"]:
                    proposal.status = "rejected"
                    proposal.notes = f"Invariant violation: {param} lower >= upper"
                    prop_repo.update(proposal)
                    return "rejected_due_to_invariants", None
            
            new_cv = CorridorVersion(
                version_tag=new_v,
                bounds=new_bounds,
                created_at=decided_at,
                evidence=proposal.evidence.get("summary", "Manual proposal"),
                is_active=True
            )
            corr_repo.add(new_cv)
            
            proposal.status = "approved"
            prop_repo.update(proposal)
            
            corridor_cache.delete("active")
            add_audit_entry("version_commit", {"version": new_v, "proposal_id": prop_id}, user_id)
            return "approved", new_v

    # File-backed
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
    proposal["decided_by"] = user_id
    
    if decision == "reject":
        proposal["status"] = "rejected"
        write_json(REGISTRY_FILE, registry)
        add_audit_entry("proposal_rejected", {"proposal_id": prop_id, "notes": notes}, user_id)
        return "rejected", None
    
    # Approve
    active_v = corridor_data["active_version"]
    new_v = next_version(active_v)
    current_bounds = corridor_data["versions"][active_v]["bounds"]
    
    new_bounds = {k: v.copy() for k, v in current_bounds.items()}
    for key, val in proposal["delta"].items():
        if "_" in key:
            param, bound_type = key.rsplit("_", 1)
            if param in new_bounds and bound_type in ["lower", "upper"]:
                limit = DELTA_LIMITS.get(param, 1.0)
                clamped_val = max(-limit, min(limit, val))
                new_val = new_bounds[param][bound_type] + clamped_val
                new_bounds[param][bound_type] = round(new_val, 2)
                
    for param, bounds in new_bounds.items():
        if bounds["lower"] >= bounds["upper"]:
             proposal["status"] = "rejected"
             proposal["notes"] = f"Invariant violation: {param} lower >= upper"
             write_json(REGISTRY_FILE, registry)
             return "rejected_due_to_invariants", None

    corridor_data["versions"][new_v] = {
        "bounds": new_bounds,
        "created_at": decided_at,
        "evidence": proposal["evidence"].get("summary", "Manual proposal")
    }
    corridor_data["active_version"] = new_v
    write_json(CORRIDOR_FILE, corridor_data)
    
    proposal["status"] = "approved"
    registry["active_version"] = new_v
    if "history" not in registry: registry["history"] = []
    registry["history"].append({
        "version": new_v,
        "at": decided_at,
        "notes": notes or f"Approved {prop_id}"
    })
    write_json(REGISTRY_FILE, registry)
    
    corridor_cache.delete("active")
    add_audit_entry("version_commit", {"version": new_v, "proposal_id": prop_id}, user_id)
    return "approved", new_v

def get_pending_proposals():
    if is_db_enabled():
        with SessionLocal() as db:
            repo = ProposalRepository(db)
            items = repo.get_all(status="pending")
            return [
                {
                    "id": p.proposal_id,
                    "delta": p.delta,
                    "evidence": p.evidence,
                    "status": p.status,
                    "created_at": p.created_at.isoformat() + "Z"
                } for p in items
            ]
    registry = read_json(REGISTRY_FILE)
    return [p for p in registry.get("proposals", []) if p["status"] == "pending"]

def get_all_proposals(status: Optional[str] = None):
    if is_db_enabled():
        with SessionLocal() as db:
            repo = ProposalRepository(db)
            items = repo.get_all(status=status)
            return [
                {
                    "id": p.proposal_id,
                    "delta": p.delta,
                    "evidence": p.evidence,
                    "status": p.status,
                    "created_at": p.created_at.isoformat() + "Z",
                    "decided_at": p.decided_at.isoformat() + "Z" if p.decided_at else None,
                    "decided_by": p.decided_by,
                    "notes": p.notes
                } for p in items
            ]
    registry = read_json(REGISTRY_FILE)
    proposals = registry.get("proposals", [])
    if status:
        proposals = [p for p in proposals if p["status"] == status]
    return proposals

def get_corridor_diff(from_v: str, to_v: str):
    if is_db_enabled():
        with SessionLocal() as db:
            repo = CorridorRepository(db)
            v1_obj = repo.get_version(from_v)
            v2_obj = repo.get_version(to_v)
            if not v1_obj or not v2_obj:
                return None
            v1_bounds = v1_obj.bounds
            v2_bounds = v2_obj.bounds
    else:
        corridor_data = read_json(CORRIDOR_FILE)
        v1 = corridor_data["versions"].get(from_v)
        v2 = corridor_data["versions"].get(to_v)
        if not v1 or not v2:
            return None
        v1_bounds = v1["bounds"]
        v2_bounds = v2["bounds"]
    
    changes = {}
    params = set(v1_bounds.keys()) | set(v2_bounds.keys())
    
    for p in params:
        b1 = v1_bounds.get(p, {"lower": 0, "upper": 0})
        b2 = v2_bounds.get(p, {"lower": 0, "upper": 0})
        changes[p] = {
            "lower": {"from": b1["lower"], "to": b2["lower"]},
            "upper": {"from": b1["upper"], "to": b2["upper"]}
        }
        
    impact_hints = {
        "energy": "likely stable",
        "quality": "likely stable",
        "yield": "likely stable"
    }
    
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

def rollback_version(target_v: str, user_id: str = "system") -> Tuple[bool, str]:
    if is_db_enabled():
        with SessionLocal() as db:
            repo = CorridorRepository(db)
            target = repo.get_version(target_v)
            if not target:
                return False, "Target version not found"
            
            repo.set_active(target_v)
            add_audit_entry("version_rollback", {"target_version": target_v}, user_id)
            corridor_cache.delete("active")
            return True, f"Rolled back to {target_v}"

    # File-backed
    corridor_data = read_json(CORRIDOR_FILE)
    if target_v not in corridor_data["versions"]:
        return False, "Target version not found"
    
    corridor_data["active_version"] = target_v
    write_json(CORRIDOR_FILE, corridor_data)
    
    # Update registry history
    registry = read_json(REGISTRY_FILE)
    registry["active_version"] = target_v
    if "history" not in registry: registry["history"] = []
    registry["history"].append({
        "version": target_v,
        "at": datetime.utcnow().isoformat() + "Z",
        "notes": f"Rollback to {target_v}"
    })
    write_json(REGISTRY_FILE, registry)
    
    add_audit_entry("version_rollback", {"target_version": target_v}, user_id)
    corridor_cache.delete("active")
    return True, f"Rolled back to {target_v}"
