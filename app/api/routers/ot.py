from fastapi import APIRouter, Depends, HTTPException
from app.api.services.ot_connector import ot_connector
from app.api.utils.security import check_role
from pydantic import BaseModel

router = APIRouter()

class ArmRequest(BaseModel):
    batch_id: str
    duration_sec: int

@router.post("/arm")
async def arm_ot(req: ArmRequest, user: dict = Depends(check_role(["Operator", "Admin"]))):
    success = ot_connector.arm(req.duration_sec)
    return {"success": success, "status": ot_connector.get_status()}

@router.get("/status")
async def get_ot_status(user: dict = Depends(check_role(["Operator", "Engineer", "Admin"]))):
    return ot_connector.get_status()

@router.post("/disarm")
async def disarm_ot(user: dict = Depends(check_role(["Operator", "Admin"]))):
    ot_connector.disarm()
    return {"success": True, "status": ot_connector.get_status()}
