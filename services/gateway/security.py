from typing import Dict, Any
from fastapi import HTTPException
import jwt
from .config import GATEWAY_JWT_SECRET, GATEWAY_VALIDATE_AUD

MOCK_TOKENS = {
    "op_01": {"sub": "op_01", "role": "Operator"},
    "eng_01": {"sub": "eng_01", "role": "Engineer"},
    "admin_01": {"sub": "admin_01", "role": "Admin"},
    "system_01": {"sub": "system_01", "role": "System"}
}

def extract_claims(token: str) -> Dict[str, Any]:
    if token in MOCK_TOKENS:
        return MOCK_TOKENS[token]
        
    try:
        options = {"verify_aud": GATEWAY_VALIDATE_AUD}
        claims = jwt.decode(token, GATEWAY_JWT_SECRET, algorithms=["HS256", "RS256"], options=options)
        return claims
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
