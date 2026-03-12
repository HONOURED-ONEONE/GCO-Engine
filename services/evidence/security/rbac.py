from fastapi import Header, HTTPException, Depends
from typing import Optional

# Local dev role mapping: op_01->Operator, eng_01->Engineer, admin_01->Admin
ROLE_MAP = {
    "op_01": "Operator",
    "eng_01": "Engineer",
    "admin_01": "Admin"
}

def get_current_user_role(x_user_id: Optional[str] = Header(None, alias="X-User-Id")):
    if not x_user_id:
        return "Unknown"
    return ROLE_MAP.get(x_user_id, "Unknown")

def require_roles(allowed_roles: list[str]):
    def role_checker(role: str = Depends(get_current_user_role)):
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return role
    return role_checker

def get_request_id(x_request_id: Optional[str] = Header(None, alias="X-Request-Id")):
    return x_request_id
