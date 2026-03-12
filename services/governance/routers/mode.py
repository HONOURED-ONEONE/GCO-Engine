from fastapi import APIRouter, HTTPException, Depends
from services.governance.models.schemas import ModeSetRequest, ModeSetResponse, ModeCurrentResponse, ModePolicyResponse
from services.governance.services.mode import set_mode, get_current_mode_data, get_policy
from services.governance.utils.security import check_role

router = APIRouter()

@router.post("/set", response_model=ModeSetResponse)
async def set_optimization_mode(request: ModeSetRequest, user: dict = Depends(check_role(["Operator", "Admin"]))):
    try:
        response_data, _ = set_mode(request.mode, user["id"])
        return ModeSetResponse(**response_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail={
            "error": "invalid_mode",
            "allowed": ["sustainability_first", "production_first"],
            "message": str(e)
        })

@router.get("/current", response_model=ModeCurrentResponse)
async def get_current_mode(user: dict = Depends(check_role(["Operator", "Engineer", "Admin"]))):
    data = get_current_mode_data()
    return ModeCurrentResponse(**data)

@router.get("/policy", response_model=ModePolicyResponse)
async def get_mode_policy(user: dict = Depends(check_role(["Operator", "Engineer", "Admin"]))):
    allowed_modes = get_policy()
    return ModePolicyResponse(
        allowed_modes=allowed_modes,
        notes="Weights are managed via Policy Registry in Phase 4."
    )
