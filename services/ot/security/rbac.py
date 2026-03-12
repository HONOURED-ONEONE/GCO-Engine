from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

def extract_claims(token: str) -> dict:
    try:
        # For demo purposes, we don't verify the signature here, gateway does it.
        # In real world, OT service would also verify.
        return jwt.decode(token, options={"verify_signature": False})
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
