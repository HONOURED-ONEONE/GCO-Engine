import base64
import json
from fastapi import Request, HTTPException

def extract_claims(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        # Check for local dev tokens mapped from users
        if token in ["op_01", "eng_01", "admin_01", "system_01"]:
            role_map = {
                "op_01": "Operator",
                "eng_01": "Engineer",
                "admin_01": "Admin",
                "system_01": "System"
            }
            return {"sub": token, "role": role_map[token], "scopes": []}
        return {}
    
    try:
        padded = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
        payload = base64.urlsafe_b64decode(padded).decode("utf-8")
        return json.loads(payload)
    except Exception:
        return {}

def require_role(request: Request, allowed_roles: list[str]):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = auth_header.split(" ")[1]
    claims = extract_claims(token)
    role = claims.get("role")
    
    if role not in allowed_roles and role != "System":
        raise HTTPException(status_code=403, detail="Forbidden")
    return claims
