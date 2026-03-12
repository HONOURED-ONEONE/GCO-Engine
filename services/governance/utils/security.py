import os
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

SECURITY_MODE = os.environ.get("SECURITY_MODE", "dev").lower()
GATEWAY_JWT_SECRET = os.environ.get("GATEWAY_JWT_SECRET", "secret")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "RS256")
JWT_AUDIENCE = os.environ.get("JWT_AUDIENCE", "gco-services")
JWT_ISSUER = os.environ.get("JWT_ISSUER", "gco-engine")

# Mock users for dev mode
MOCK_USERS = {
    "op_01": {"role": "Operator", "name": "Alice", "id": "op_01"},
    "eng_01": {"role": "Engineer", "name": "Bob", "id": "eng_01"},
    "admin_01": {"role": "Admin", "name": "Charlie", "id": "admin_01"},
    "system_01": {"role": "System", "name": "System", "id": "system_01"}
}

def get_current_user(auth: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    token = auth.credentials
    
    if SECURITY_MODE == "dev" and token in MOCK_USERS:
        return MOCK_USERS[token]
        
    try:
        # In prod, we strictly validate
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
        # Map claims to user dict
        return {
            "id": claims.get("sub"),
            "role": claims.get("role"),
            "name": claims.get("name", claims.get("sub"))
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token or authentication failed")

def check_role(roles: List[str]):
    def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail=f"Role {user['role']} not authorized. Required: {roles}")
        return user
    return role_checker
