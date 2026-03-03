import time
import asyncio
from typing import Dict, Any, Optional
from app.api.utils.io import read_json, write_json, BASE_DATA_DIR
import os

OT_CONFIG_FILE = os.path.join(BASE_DATA_DIR, "ot_config.json")

class OTConnector:
    def __init__(self):
        self.mode = "shadow" # "shadow" or "guarded"
        self.armed = False
        self.arm_expiry = 0
        self.last_write = None
        self.connected = False
        self._init_config()

    def _init_config(self):
        if not os.path.exists(OT_CONFIG_FILE):
            write_json(OT_CONFIG_FILE, {
                "mode": "shadow",
                "armed": False,
                "interlocks": {
                    "corridor_stable_sec": 30,
                    "max_rate_t": 2.0,
                    "max_rate_f": 0.5
                },
                "alarms": []
            })
        config = read_json(OT_CONFIG_FILE)
        self.mode = config.get("mode", "shadow")
        self.armed = config.get("armed", False)

    def arm(self, duration_sec: int):
        self.armed = True
        self.arm_expiry = time.time() + duration_sec
        self._save_config()
        return True

    def disarm(self):
        self.armed = False
        self._save_config()

    def _save_config(self):
        write_json(OT_CONFIG_FILE, {
            "mode": self.mode,
            "armed": self.armed,
            "last_write": self.last_write
        })

    def get_status(self):
        # Auto-expiry of arming
        if self.armed and time.time() > self.arm_expiry:
            self.armed = False
            self._save_config()

        return {
            "mode": self.mode,
            "armed": self.armed,
            "arm_remaining_sec": max(0, int(self.arm_expiry - time.time())) if self.armed else 0,
            "connected": True, # Mocked
            "last_write": self.last_write
        }

    async def write_setpoint(self, setpoints: Dict[str, float], batch_id: str):
        status = self.get_status()
        
        # Condition 1: Armed
        if not status["armed"]:
            return False, "Not armed for write-back"
        
        # Condition 2: Guarded mode
        # In shadow mode, we just log the recommendation
        if self.mode == "shadow":
            self.last_write = {"ts": time.time(), "setpoints": setpoints, "status": "shadow_logged"}
            return True, "Shadow mode: logged only"

        # Condition 3: No active alarms (Mocked)
        alarms = [] # In real world, check SCADA
        if alarms:
            return False, f"Active alarms: {alarms}"

        # Perform Write (Mocked)
        # await self.client.write(setpoints)
        self.last_write = {"ts": time.time(), "setpoints": setpoints, "status": "success", "batch_id": batch_id}
        self._save_config()
        return True, "Write successful"

ot_connector = OTConnector()
