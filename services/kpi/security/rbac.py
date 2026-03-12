import os
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, Security, Depends, Header
import jwt

SECURITY_MODE = os.environ.get("SECURITY_MODE", "dev").lower()
GATEWAY_JWT_SECRET = os.environ.get("GATEWAY_JWT_SECRET", "secret")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "RS256")
JWT_AUDIENCE = os.environ.get("JWT_AUDIENCE", "gco-services")
JWT_ISSUER = os.environ.get("JWT_ISSUER", "gco-engine")

# Mock users for dev mode
MOCK_USERS = {
    "op_01": "Operator",
    "eng_01": "Engineer",
    "admin_01": "Admin",
    "system_01": "System"
}

def get_current_role(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
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
        raise HTTPException(status_code=401, detail="Invalid token or authentication failed")

def get_current_subject(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        return "anonymous"
    token = authorization.replace("Bearer ", "").strip()
    if SECURITY_MODE == "dev" and token in MOCK_USERS:
        return token
    try:
        claims = jwt.decode(token, options={"verify_signature": False})
        return claims.get("sub", "unknown")
    except:
        return token

def require_roles(allowed_roles: list[str]):
    def role_checker(role: str = Depends(get_current_role)):
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail=f"Forbidden: Insufficient privileges. Required: {allowed_roles}")
        return role
    return role_checker

require_operator = require_roles(["Operator", "Engineer", "Admin", "System"])
require_engineer = require_roles(["Engineer", "Admin", "System"])
