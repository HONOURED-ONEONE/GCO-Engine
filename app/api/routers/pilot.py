from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict
from app.api.services.pilot import pilot_service

router = APIRouter()

class PilotStartRequest(BaseModel):
    pilot_id: str
    twin_session_id: str
    schedule: Dict
    mode: str
    canary_batches: Optional[int] = 3

class PilotStopRequest(BaseModel):
    pilot_id: str

@router.post("/start")
async def start_pilot(req: PilotStartRequest):
    res = await pilot_service.start_pilot(req.pilot_id, req.twin_session_id, req.schedule, req.mode, req.canary_batches)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@router.post("/stop")
async def stop_pilot(req: PilotStopRequest):
    return await pilot_service.stop_pilot()

@router.get("/health")
async def get_health(pilot_id: str):
    return pilot_service.get_health()

@router.get("/snapshot")
async def get_snapshot(pilot_id: str):
    return pilot_service.get_snapshot()
