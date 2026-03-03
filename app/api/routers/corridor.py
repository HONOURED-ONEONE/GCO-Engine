from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from app.api.models.schemas import (
    CorridorVersionResponse, 
    CorridorApproveRequest, 
    CorridorApproveResponse, 
    CorridorProposeRequest, 
    CorridorProposeResponse,
    CorridorProposalsResponse,
    CorridorAuditResponse,
    CorridorDiffResponse
)
from app.api.services.corridor import (
    get_active_corridor, 
    get_version_history, 
    approve_proposal, 
    propose_corridor_change,
    get_all_proposals,
    get_corridor_diff
)
from app.api.utils.audit import get_audit_entries
from app.api.utils.security import check_role

router = APIRouter()

@router.get("/version", response_model=CorridorVersionResponse)
async def corridor_version(user: dict = Depends(check_role(["Operator", "Engineer", "Admin"]))):
    active_v, active_data = get_active_corridor()
    history = get_version_history()
    return CorridorVersionResponse(
        active_version=active_v,
        bounds=active_data["bounds"],
        history=history
    )

@router.post("/propose", response_model=CorridorProposeResponse)
async def propose(request: CorridorProposeRequest, user: dict = Depends(check_role(["Engineer", "Admin"]))):
    prop_id = propose_corridor_change(request.delta, request.evidence.dict())
    return CorridorProposeResponse(proposal_id=prop_id, status="pending")

@router.post("/approve", response_model=CorridorApproveResponse)
async def approve(request: CorridorApproveRequest, user: dict = Depends(check_role(["Operator", "Admin"]))):
    status, new_v = approve_proposal(request.proposal_id, request.decision, request.notes, user["id"])
    
    if status.startswith("rejected"):
        return CorridorApproveResponse(
            status=status, 
            message=f"Proposal {request.proposal_id} was {status}.",
            cache_invalidation=[]
        )
    
    if status == "Not found":
        raise HTTPException(status_code=404, detail="Proposal not found")
        
    _, active_data = get_active_corridor()
    
    return CorridorApproveResponse(
        status=status, 
        new_version=new_v,
        active_bounds=active_data["bounds"],
        cache_invalidation=["corridor_bounds"],
        message="Corridor updated and activated."
    )

@router.get("/proposals", response_model=CorridorProposalsResponse)
async def list_proposals(status: Optional[str] = Query(None, regex="^(pending|approved|rejected)$"), user: dict = Depends(check_role(["Operator", "Engineer", "Admin"]))):
    items = get_all_proposals(status)
    return CorridorProposalsResponse(items=items)

@router.get("/audit", response_model=CorridorAuditResponse)
async def corridor_audit(limit: int = Query(100, ge=1, le=500), user: dict = Depends(check_role(["Admin"]))):
    items = get_audit_entries(limit)
    return CorridorAuditResponse(items=items)

@router.get("/diff", response_model=CorridorDiffResponse)
async def corridor_diff(from_v: str, to_v: str, user: dict = Depends(check_role(["Engineer", "Admin"]))):
    diff = get_corridor_diff(from_v, to_v)
    if not diff:
        raise HTTPException(status_code=404, detail="One or both versions not found")
    return CorridorDiffResponse(**diff)
