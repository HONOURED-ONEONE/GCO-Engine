import os
from typing import Optional, List, Dict, Any
from fastapi import Request, HTTPException, Depends
import jwt

SECURITY_MODE = os.environ.get("SECURITY_MODE", "dev").lower()
GATEWAY_JWT_SECRET = os.environ.get("GATEWAY_JWT_SECRET", "secret")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "RS256")
JWT_AUDIENCE = os.environ.get("JWT_AUDIENCE", "gco-services")
JWT_ISSUER = os.environ.get("JWT_ISSUER", "gco-engine")

MOCK_USERS = {
    "op_01": "Operator",
    "eng_01": "Engineer",
    "admin_01": "Admin",
    "system_01": "System"
}

def extract_role(req: Request) -> str:
    authorization = req.headers.get("Authorization", "")
    if not authorization:
        return "Unknown"
        
    token = authorization.replace("Bearer ", "").strip()
    
    if SECURITY_MODE == "dev" and token in MOCK_USERS:
        return MOCK_USERS[token]
        
    try:
        options = {
            "verify_aud": True,
            "verify_iss": SECURITY_MODE == "prod",
            "require": ["exp", "sub", "role"] if SECURITY_MODE == "prod" else []
        }
        
        claims = jwt.decode(
            token, 
            GATEWAY_JWT_SECRET, 
            algorithms=[JWT_ALGORITHM, "HS256"], 
            options=options,
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER if SECURITY_MODE == "prod" else None
        )
        return claims.get("role", "Unknown")
    except Exception:
        return "Unknown"

def require_role(allowed_roles: list):
    def dependency(req: Request):
        role = extract_role(req)
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail=f"Forbidden: {role} not in {allowed_roles}")
        return role
    return dependency
