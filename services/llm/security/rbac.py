import os
from typing import Optional, List, Dict, Any
from fastapi import Request, HTTPException
import jwt

SECURITY_MODE = os.environ.get("SECURITY_MODE", "dev").lower()
GATEWAY_JWT_SECRET = os.environ.get("GATEWAY_JWT_SECRET", "secret")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "RS256")
JWT_AUDIENCE = os.environ.get("JWT_AUDIENCE", "gco-services")
JWT_ISSUER = os.environ.get("JWT_ISSUER", "gco-engine")

MOCK_USERS = {
    "op_01": {"role": "Operator", "sub": "op_01"},
    "eng_01": {"role": "Engineer", "sub": "eng_01"},
    "admin_01": {"role": "Admin", "sub": "admin_01"},
    "system_01": {"role": "System", "sub": "system_01"}
}

def extract_claims(token: str) -> dict:
    if SECURITY_MODE == "dev" and token in MOCK_USERS:
        return MOCK_USERS[token]
        
    try:
        options = {
            "verify_aud": True,
            "verify_iss": SECURITY_MODE == "prod",
            "require": ["exp", "sub", "role"] if SECURITY_MODE == "prod" else []
        }
        
        return jwt.decode(
            token, 
            GATEWAY_JWT_SECRET, 
            algorithms=[JWT_ALGORITHM, "HS256"], 
            options=options,
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER if SECURITY_MODE == "prod" else None
        )
    except Exception:
        return {}

def require_role(request: Request, allowed_roles: list[str]):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    token = auth_header.replace("Bearer ", "").strip()
    claims = extract_claims(token)
    role = claims.get("role")
    
    if role not in allowed_roles and role != "System":
        raise HTTPException(status_code=403, detail=f"Forbidden: role {role} not in {allowed_roles}")
    return claims
