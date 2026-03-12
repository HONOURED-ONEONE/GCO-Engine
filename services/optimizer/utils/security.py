from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

def check_role(allowed_roles: list):
    def _check(credentials: HTTPAuthorizationCredentials = Depends(security)):
        token = credentials.credentials
        # token-as-user-id for dev
        roles_map = {
            "op_01": "Operator",
            "eng_01": "Engineer",
            "admin_01": "Admin",
            "system_01": "System"
        }
        
        user_role = None
        if token in roles_map:
            user_role = roles_map[token]
        else:
            # Check if it's a real JWT fallback
            try:
                claims = jwt.decode(token, options={"verify_signature": False})
                user_role = claims.get("role")
            except:
                pass
                
        if not user_role or user_role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden: Insufficient role")
        
        return {"sub": token, "role": user_role}
    return _check
