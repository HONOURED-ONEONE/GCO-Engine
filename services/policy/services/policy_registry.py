import json
import os
from filelock import FileLock

REGISTRY_FILE = "data/policy_registry.json"
LOCK_FILE = "data/policy_registry.lock"

def _load_reg():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(REGISTRY_FILE):
        return {"active": None, "items": []}
    with open(REGISTRY_FILE, "r") as f:
        try:
            data = json.load(f)
            if "items" not in data:
                data["items"] = []
            return data
        except Exception:
            return {"active": None, "items": []}

def _save_reg(data):
    with open(REGISTRY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def list_policies():
    return _load_reg().get("items", [])

def add_or_update_policy(p_id: str, data: dict):
    with FileLock(LOCK_FILE):
        reg = _load_reg()
        found = False
        for item in reg["items"]:
            if item["id"] == p_id:
                item.update(data)
                found = True
                break
        if not found:
            data["id"] = p_id
            reg["items"].append(data)
        _save_reg(reg)

def activate_policy(p_id: str):
    with FileLock(LOCK_FILE):
        reg = _load_reg()
        reg["active"] = p_id
        _save_reg(reg)

def get_active_policy():
    reg = _load_reg()
    active_id = reg.get("active")
    for item in reg.get("items", []):
        if item["id"] == active_id:
            return active_id, item
    return active_id, {}
