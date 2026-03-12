import json
import os
import sys
from datetime import datetime

# Add root to sys.path
sys.path.append(os.getcwd())

from services.ot.db.session import SessionLocal, init_db
from services.ot.db.models import OTConfigEntry, OTStateEntry

DATA_DIR = "./data"
CONFIG_FILE = os.path.join(DATA_DIR, "ot_config.json")
STATE_FILE = os.path.join(DATA_DIR, "ot_state.json")

def migrate():
    print("Migrating OT data...")
    init_db()
    db = SessionLocal()
    
    # 1. OT Config
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try:
                data = json.load(f)
                if data:
                    entry = OTConfigEntry(config=data)
                    db.add(entry)
            except:
                pass
    
    # 2. OT State
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                data = json.load(f)
                if data:
                    entry = OTStateEntry(
                        mode=data.get("mode", "shadow"),
                        armed=data.get("armed", False),
                        last_write=data.get("last_write"),
                        last_good_setpoint=data.get("last_good_setpoint", {}),
                        last_readback=data.get("last_readback", {}),
                        connector_state=data.get("connector_state", "disconnected")
                    )
                    db.add(entry)
            except:
                pass

    db.commit()
    db.close()
    print("OT migration complete.")

if __name__ == "__main__":
    migrate()
