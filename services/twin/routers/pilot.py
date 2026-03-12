from fastapi import APIRouter, HTTPException, Depends
from ..models.schemas import (
    PilotStartRequest, PilotStartResponse, PilotHealthResponse, PilotSnapshotResponse, PilotStopRequest
)
from ..services.pilot_engine import pilot_engine
from ..utils.metrics import metrics_tracker
from ..security.rbac import require_role, OPERATOR_ENGINEER_ADMIN

router = APIRouter()

@router.post("/start", response_model=PilotStartResponse, dependencies=[Depends(require_role(OPERATOR_ENGINEER_ADMIN))])
async def start_pilot(req: PilotStartRequest):
    metrics_tracker.pilots_started += 1
    ctx = await pilot_engine.start_pilot(req)
    if not ctx:
        raise HTTPException(status_code=400, detail="Could not start pilot")
    return PilotStartResponse(pilot_id=req.pilot_id, status="running")

@router.get("/health", response_model=PilotHealthResponse)
async def get_health(pilot_id: str):
    res = pilot_engine.get_health(pilot_id)
    if not res:
        raise HTTPException(status_code=404, detail="Pilot not found")
    return res

@router.get("/snapshot", response_model=PilotSnapshotResponse)
async def get_snapshot(pilot_id: str):
    res = pilot_engine.get_snapshot(pilot_id)
    if not res:
        raise HTTPException(status_code=404, detail="Pilot not found")
    return res

@router.post("/stop", dependencies=[Depends(require_role(OPERATOR_ENGINEER_ADMIN))])
async def stop_pilot(req: PilotStopRequest):
    stopped = pilot_engine.stop_pilot(req.pilot_id)
    if not stopped:
        raise HTTPException(status_code=404, detail="Pilot not found")
    return {"pilot_id": req.pilot_id, "status": "stopped"}
