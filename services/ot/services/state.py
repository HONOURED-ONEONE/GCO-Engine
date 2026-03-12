import json
import os
from filelock import FileLock
from typing import Optional, Dict, Any
from datetime import datetime
from services.ot.db.session import SessionLocal, is_db_enabled
from services.ot.repositories.ot_repository import OTRepository

DATA_DIR = "data"
CONFIG_FILE = os.path.join(DATA_DIR, "ot_config.json")
STATE_FILE = os.path.join(DATA_DIR, "ot_state.json")
CONFIG_LOCK = CONFIG_FILE + ".lock"
STATE_LOCK = STATE_FILE + ".lock"

class StateManager:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self._ensure_files()

    def _ensure_files(self):
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "w") as f:
                json.dump({}, f)
        if not os.path.exists(STATE_FILE):
            with open(STATE_FILE, "w") as f:
                json.dump({
                    "mode": "shadow",
                    "armed": False,
                    "last_write": None,
                    "last_good_setpoint": {},
                    "last_readback": {},
                    "connector_state": "disconnected"
                }, f)

    def get_config(self) -> Optional[Dict[str, Any]]:
        if is_db_enabled():
            with SessionLocal() as db:
                repo = OTRepository(db)
                return repo.get_config()

        with FileLock(CONFIG_LOCK):
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return data if data else None

    def save_config(self, config: Dict[str, Any]):
        if is_db_enabled():
            with SessionLocal() as db:
                repo = OTRepository(db)
                repo.save_config(config)
                return

        with FileLock(CONFIG_LOCK):
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=2)

    def get_state(self) -> Dict[str, Any]:
        if is_db_enabled():
            with SessionLocal() as db:
                repo = OTRepository(db)
                return repo.get_state()

        with FileLock(STATE_LOCK):
            with open(STATE_FILE, "r") as f:
                return json.load(f)

    def update_state(self, updates: Dict[str, Any]):
        if is_db_enabled():
            with SessionLocal() as db:
                repo = OTRepository(db)
                repo.update_state(updates)
                return

        with FileLock(STATE_LOCK):
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
            state.update(updates)
            serializable_state = self._make_serializable(state)
            with open(STATE_FILE, "w") as f:
                json.dump(serializable_state, f, indent=2)

    def _make_serializable(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: self._make_serializable(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._make_serializable(v) for v in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        return data

state_manager = StateManager()
