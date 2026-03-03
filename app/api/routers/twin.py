from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.api.services.twin import twin_service

router = APIRouter()

class TwinStartRequest(BaseModel):
    scenario_id: str
    seed: Optional[int] = 4269
    batch_count: Optional[int] = 10
    opcua: Optional[bool] = False

class TwinStopRequest(BaseModel):
    twin_session_id: str

@router.post("/start")
async def start_twin(req: TwinStartRequest):
    res = await twin_service.start_twin(req.scenario_id, req.seed, req.batch_count, req.opcua)
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@router.post("/stop")
async def stop_twin(req: TwinStopRequest):
    return await twin_service.stop_twin()

@router.get("/status")
async def get_status(session: Optional[str] = None):
    return twin_service.get_status()

@router.get("/scenarios")
async def get_scenarios():
    return twin_service.get_scenarios()
