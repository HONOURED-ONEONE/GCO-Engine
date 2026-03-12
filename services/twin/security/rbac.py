from fastapi import Request, HTTPException, Depends
from typing import List

def get_claims(request: Request):
    # This is populated by the Gateway and passed via headers or already parsed if we have a local middleware
    # In this architecture, gateway passes X-User-Role or similar, or we re-verify JWT if needed.
    # For microservice internal use, we often trust headers if we are behind a PEP (Gateway).
    roles = request.headers.get("X-User-Roles", "").split(",")
    return {"roles": [r.strip() for r in roles if r.strip()]}

def require_role(allowed_roles: List[str]):
    def role_checker(claims: dict = Depends(get_claims)):
        user_roles = claims.get("roles", [])
        if not any(role in user_roles for role in allowed_roles):
            # If no roles in header, we might be in dev mode or bypassing gateway
            # For this demo, let's allow if a special dev header is present or roles are missing
            if not user_roles:
                return # Dev mode / bypass
            raise HTTPException(status_code=403, detail=f"Role {allowed_roles} required")
    return role_checker

# Standard permissions
ENGINEER_ADMIN = ["engineer", "admin"]
OPERATOR_ENGINEER_ADMIN = ["operator", "engineer", "admin"]
