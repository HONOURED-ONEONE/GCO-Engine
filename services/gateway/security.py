from typing import Dict, Any
from fastapi import HTTPException
import jwt
import os
from .config import (
    GATEWAY_JWT_SECRET, GATEWAY_VALIDATE_AUD, SECURITY_MODE, 
    JWT_ISSUER, JWT_AUDIENCE, JWT_ALGORITHM
)

MOCK_TOKENS = {
    "op_01": {"sub": "op_01", "role": "Operator"},
    "eng_01": {"sub": "eng_01", "role": "Engineer"},
    "admin_01": {"sub": "admin_01", "role": "Admin"},
    "system_01": {"sub": "system_01", "role": "System"}
}

def extract_claims(token: str) -> Dict[str, Any]:
    if SECURITY_MODE == "dev" and token in MOCK_TOKENS:
        return MOCK_TOKENS[token]
        
    try:
        # In prod, we strictly validate
        options = {
            "verify_aud": GATEWAY_VALIDATE_AUD,
            "verify_iss": SECURITY_MODE == "prod",
            "require": ["exp", "sub", "role"] if SECURITY_MODE == "prod" else []
        }
        
        # In a real prod setup, we would use a JWKS client here.
        # For now, we use the secret-based decoding as a fallback.
        claims = jwt.decode(
            token, 
            GATEWAY_JWT_SECRET, 
            algorithms=[JWT_ALGORITHM, "HS256"], 
            options=options,
            audience=JWT_AUDIENCE if GATEWAY_VALIDATE_AUD else None,
            issuer=JWT_ISSUER if SECURITY_MODE == "prod" else None
        )
        return claims
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")
