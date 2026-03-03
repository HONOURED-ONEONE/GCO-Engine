from typing import List
from fastapi import APIRouter
from app.api.models.schemas import (
    CorridorVersionResponse, 
    CorridorApproveRequest, 
    CorridorApproveResponse, 
    CorridorProposeRequest, 
    CorridorProposeResponse
)
from app.api.services.corridor import (
    get_active_corridor, 
    get_version_history, 
    approve_proposal, 
    propose_corridor_change,
    get_pending_proposals
)

router = APIRouter()

@router.get("/version", response_model=CorridorVersionResponse)
async def corridor_version():
    active_v, active_data = get_active_corridor()
    history = get_version_history()
    return CorridorVersionResponse(
        active_version=active_v,
        bounds=active_data["bounds"],
        history=history
    )

@router.post("/propose", response_model=CorridorProposeResponse)
async def propose(request: CorridorProposeRequest):
    # This can be called by internal services (marl.py) or via API
    prop_id = propose_corridor_change(request.delta, request.evidence)
    return CorridorProposeResponse(proposal_id=prop_id, status="pending")

@router.post("/approve", response_model=CorridorApproveResponse)
async def approve(request: CorridorApproveRequest):
    status, new_v = approve_proposal(request.proposal_id, request.decision, request.notes)
    return CorridorApproveResponse(status=status, new_version=new_v)

@router.get("/proposals/pending")
async def pending_proposals():
    return get_pending_proposals()
