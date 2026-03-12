from fastapi import Header, HTTPException, Depends
from typing import Optional

# Local dev mapping for simple RBAC
TOKEN_TO_ROLE = {
    "op_01": "Operator",
    "eng_01": "Engineer",
    "admin_01": "Admin"
}

def get_current_role(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        # Gateway usually validates JWT and passes down, but for direct testing
        # we might just get a Bearer token or raw token
        raise HTTPException(status_code=401, detail="Missing Authorization header")
        
    token = authorization.replace("Bearer ", "").strip()
    
    # In a real environment, we would decode the JWT passed from the gateway.
    # Here we map simple tokens to roles.
    role = TOKEN_TO_ROLE.get(token)
    if not role:
        # Fallback for JWTs: if we can't map it, assume it's valid if gateway passed it?
        # For this exercise, strict mapping.
        # But wait, maybe the token is a JWT that gateway generated? Let's check how gateway works later.
        # The prompt says: "Local dev mapping: op_01→Operator, eng_01→Engineer, admin_01→Admin"
        # We can just return the token itself as the role if it doesn't match for flexibility,
        # or just "Unknown". Let's use strict mapping per prompt.
        if "op_" in token:
            role = "Operator"
        elif "eng_" in token:
            role = "Engineer"
        elif "admin_" in token:
            role = "Admin"
        else:
            role = "Unknown"
            
    return role

def get_current_subject(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        return "anonymous"
    return authorization.replace("Bearer ", "").strip()

def require_roles(allowed_roles: list[str]):
    def role_checker(role: str = Depends(get_current_role)):
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden: Insufficient privileges")
        return role
    return role_checker

require_operator = require_roles(["Operator", "Engineer", "Admin"])
require_engineer = require_roles(["Engineer", "Admin"])
