import json
import os
from filelock import FileLock
from datetime import datetime
from services.policy.db.session import SessionLocal, is_db_enabled
from services.policy.repositories.policy_repository import PolicyRepository

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
    if is_db_enabled():
        with SessionLocal() as db:
            repo = PolicyRepository(db)
            entries = repo.get_all()
            return [
                {
                    "id": e.policy_id,
                    "hash": e.hash,
                    "created_at": e.created_at.timestamp(),
                    "metrics": e.metrics,
                    "description": e.description
                } for e in entries
            ]

    return _load_reg().get("items", [])

def add_or_update_policy(p_id: str, data: dict):
    if is_db_enabled():
        with SessionLocal() as db:
            repo = PolicyRepository(db)
            # data in memory has created_at as timestamp
            created_at = data.get("created_at")
            if isinstance(created_at, (int, float)):
                created_at = datetime.fromtimestamp(created_at)
            
            repo.add_or_update(p_id, {
                "hash": data.get("hash"),
                "created_at": created_at or datetime.utcnow(),
                "metrics": data.get("metrics"),
                "description": data.get("description")
            })
            return

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
    if is_db_enabled():
        with SessionLocal() as db:
            repo = PolicyRepository(db)
            repo.set_active(p_id)
            return

    with FileLock(LOCK_FILE):
        reg = _load_reg()
        reg["active"] = p_id
        _save_reg(reg)

def get_active_policy():
    if is_db_enabled():
        with SessionLocal() as db:
            repo = PolicyRepository(db)
            active = repo.get_active()
            if active:
                return active.policy_id, {
                    "id": active.policy_id,
                    "hash": active.hash,
                    "created_at": active.created_at.timestamp(),
                    "metrics": active.metrics,
                    "description": active.description
                }
            return None, {}

    reg = _load_reg()
    active_id = reg.get("active")
    for item in reg.get("items", []):
        if item["id"] == active_id:
            return active_id, item
    return active_id, {}
