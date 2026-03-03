from typing import Optional, List
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import time

security = HTTPBearer()

# Mock users for MVP
MOCK_USERS = {
    "op_01": {"role": "Operator", "name": "Alice"},
    "eng_01": {"role": "Engineer", "name": "Bob"},
    "admin_01": {"role": "Admin", "name": "Charlie"}
}

def get_current_user(auth: HTTPAuthorizationCredentials = Security(security)):
    # For MVP, we treat the token as the user_id directly
    user_id = auth.credentials
    if user_id in MOCK_USERS:
        return {**MOCK_USERS[user_id], "id": user_id}
    raise HTTPException(status_code=401, detail="Invalid token")

def check_role(roles: List[str]):
    def role_checker(user: dict = Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=403, detail=f"Role {user['role']} not authorized. Required: {roles}")
        return user
    return role_checker
