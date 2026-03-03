from fastapi import APIRouter, Depends, HTTPException
from app.api.services.marl import get_active_policy, train_offline_batch, read_json, POLICY_REGISTRY_FILE, write_json
from app.api.utils.security import check_role
from pydantic import BaseModel

router = APIRouter()

@router.get("/active")
async def get_active_policy_route(user: dict = Depends(check_role(["Operator", "Engineer", "Admin"]))):
    return get_active_policy()

@router.get("/list")
async def list_policies(user: dict = Depends(check_role(["Engineer", "Admin"]))):
    from app.api.services.marl import init_marl_files
    init_marl_files()
    return read_json(POLICY_REGISTRY_FILE).get("policies", [])

@router.post("/train")
async def train_policy(user: dict = Depends(check_role(["Engineer", "Admin"]))):
    policy, error = train_offline_batch()
    if error:
        raise HTTPException(status_code=400, detail=error)
    return policy

@router.post("/activate/{policy_id}")
async def activate_policy(policy_id: str, user: dict = Depends(check_role(["Admin"]))):
    registry = read_json(POLICY_REGISTRY_FILE)
    found = False
    for p in registry.get("policies", []):
        if p["id"] == policy_id:
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    registry["active_policy_id"] = policy_id
    write_json(POLICY_REGISTRY_FILE, registry)
    return {"success": True, "active_policy_id": policy_id}
