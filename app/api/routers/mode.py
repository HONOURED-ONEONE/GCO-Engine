from fastapi import APIRouter
from app.api.models.schemas import ModeSetRequest, ModeSetResponse
from app.api.services.mode import set_optimization_mode

router = APIRouter()

@router.post("/set", response_model=ModeSetResponse)
async def set_mode(request: ModeSetRequest):
    mode, weights = set_optimization_mode(request.mode)
    return ModeSetResponse(mode=mode, weights=weights)
