import os
from typing import Optional, List, Dict, Any
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

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

def require_role(roles: list):
    async def role_checker(request: Request, auth: HTTPAuthorizationCredentials = Security(security)):
        token = auth.credentials
        claims = extract_claims(token)
        user_role = claims.get("role")
        if user_role not in roles:
            raise HTTPException(status_code=403, detail=f"Required role: {roles}")
        return claims
    return role_checker
