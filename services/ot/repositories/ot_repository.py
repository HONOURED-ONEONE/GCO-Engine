from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from services.ot.db.models import OTConfigEntry, OTStateEntry

class OTRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_config(self) -> Optional[Dict[str, Any]]:
        entry = self.db.query(OTConfigEntry).order_by(OTConfigEntry.updated_at.desc()).first()
        return entry.config if entry else None

    def save_config(self, config: Dict[str, Any]):
        entry = OTConfigEntry(config=config)
        self.db.add(entry)
        self.db.commit()

    def get_state(self) -> Dict[str, Any]:
        entry = self.db.query(OTStateEntry).order_by(OTStateEntry.updated_at.desc()).first()
        if not entry:
            return {
                "armed": False,
                "last_write": None,
                "last_good_setpoint": {},
                "last_readback": {},
                "connector_state": "disconnected",
                "mode": "shadow"
            }
        return {
            "armed": entry.armed,
            "last_write": entry.last_write,
            "last_good_setpoint": entry.last_good_setpoint,
            "last_readback": entry.last_readback,
            "connector_state": entry.connector_state,
            "mode": entry.mode
        }

    def update_state(self, updates: Dict[str, Any]):
        entry = self.db.query(OTStateEntry).order_by(OTStateEntry.updated_at.desc()).first()
        if not entry:
            entry = OTStateEntry(
                mode=updates.get("mode", "shadow"),
                armed=updates.get("armed", False),
                last_write=updates.get("last_write"),
                last_good_setpoint=updates.get("last_good_setpoint", {}),
                last_readback=updates.get("last_readback", {}),
                connector_state=updates.get("connector_state", "disconnected")
            )
            self.db.add(entry)
        else:
            if "mode" in updates: entry.mode = updates["mode"]
            if "armed" in updates: entry.armed = updates["armed"]
            if "last_write" in updates: entry.last_write = updates["last_write"]
            if "last_good_setpoint" in updates: entry.last_good_setpoint = updates["last_good_setpoint"]
            if "last_readback" in updates: entry.last_readback = updates["last_readback"]
            if "connector_state" in updates: entry.connector_state = updates["connector_state"]
            entry.updated_at = datetime.utcnow()
        self.db.commit()
