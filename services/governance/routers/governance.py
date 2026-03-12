from fastapi import APIRouter, Depends
from typing import Dict, Any
from pydantic import BaseModel
from services.governance.utils.security import check_role
from services.governance.utils.audit import add_audit_entry, verify_audit_chain
from services.governance.services.corridor import get_active_corridor
from services.governance.services.mode import get_current_mode_data
from services.governance.utils.io import read_json, REGISTRY_FILE

router = APIRouter()

class AuditIngestRequest(BaseModel):
    event_type: str
    data: Dict[str, Any]
    user_id: str

@router.post("/audit/ingest")
async def ingest_audit(request: AuditIngestRequest, user: dict = Depends(check_role(["Admin"]))):
    add_audit_entry(request.event_type, request.data, request.user_id)
    # Re-read to get the hash
    registry = read_json(REGISTRY_FILE)
    audit = registry.get("audit", [])
    entry_hash = audit[-1].get("hash") if audit else None
    return {"status": "recorded", "hash": entry_hash}

@router.get("/audit/verify")
async def verify_audit(user: dict = Depends(check_role(["Admin", "Auditor", "Engineer"]))):
    ok, last_hash, length = verify_audit_chain()
    return {"ok": ok, "last_hash": last_hash, "length": length}

@router.get("/active")
async def get_active_state():
    # Fetch active bounds
    active_v, active_data = get_active_corridor()
    # Fetch mode data
    mode_data = get_current_mode_data()
    # Fetch audit head hash
    registry = read_json(REGISTRY_FILE)
    audit = registry.get("audit", [])
    head_hash = audit[-1].get("hash") if audit else "0"*64
    
    return {
        "active_version": active_v,
        "bounds": active_data["bounds"] if active_data else {},
        "last_mode": mode_data["mode"],
        "last_mode_weights": mode_data["weights"],
        "audit_head_hash": head_hash
    }
