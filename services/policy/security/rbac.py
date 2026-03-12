from fastapi import Request, HTTPException

def extract_role(req: Request) -> str:
    auth = req.headers.get("Authorization", "")
    if "op_" in auth:
        return "Operator"
    if "eng_" in auth:
        return "Engineer"
    if "admin_" in auth:
        return "Admin"
    return "Operator" # Default for local/tests if not strictly enforced by gateway

def require_role(allowed_roles: list):
    def dependency(req: Request):
        role = extract_role(req)
        if role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return role
    return dependency
