from fastapi import APIRouter, HTTPException
from app.api.models.schemas import ModeSetRequest, ModeSetResponse, ModeCurrentResponse, ModePolicyResponse
from app.api.services.mode import set_mode, get_current_mode_data, get_policy

router = APIRouter()

@router.post("/set", response_model=ModeSetResponse)
async def set_optimization_mode(request: ModeSetRequest):
    try:
        response_data, _ = set_mode(request.mode, request.operator_id)
        return ModeSetResponse(**response_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail={
            "error": "invalid_mode",
            "allowed": ["sustainability_first", "production_first"],
            "message": str(e)
        })

@router.get("/current", response_model=ModeCurrentResponse)
async def get_current_mode():
    data = get_current_mode_data()
    return ModeCurrentResponse(**data)

@router.get("/policy", response_model=ModePolicyResponse)
async def get_mode_policy():
    allowed_modes = get_policy()
    return ModePolicyResponse(
        allowed_modes=allowed_modes,
        notes="Weights are fixed in Phase 1. Custom policies come in later phases."
    )
