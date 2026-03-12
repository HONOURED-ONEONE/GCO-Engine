import json
import os
import sys
from datetime import datetime

# Add root to sys.path
sys.path.append(os.getcwd())

from services.policy.db.session import SessionLocal, init_db
from services.policy.db.models import PolicyEntry, ExperienceEntry

DATA_DIR = "./data"
REGISTRY_FILE = os.path.join(DATA_DIR, "policy_registry.json")
EXPERIENCE_FILE = os.path.join(DATA_DIR, "experience_store.json")

def parse_iso(dt_str):
    if not dt_str: return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except:
        return datetime.utcnow()

def migrate():
    print("Migrating Policy data...")
    init_db()
    db = SessionLocal()
    
    # 1. Policy Registry
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f:
            try:
                data = json.load(f)
            except:
                data = {"items": [], "active": None}
            
            active_id = data.get("active")
            for item in data.get("items", []):
                p_id = item.get("id")
                if not db.query(PolicyEntry).filter_by(policy_id=p_id).first():
                    created_at = item.get("created_at")
                    if isinstance(created_at, (int, float)):
                        created_at_dt = datetime.fromtimestamp(created_at)
                    else:
                        created_at_dt = parse_iso(created_at) or datetime.utcnow()
                        
                    entry = PolicyEntry(
                        policy_id=p_id,
                        hash=item.get("hash"),
                        created_at=created_at_dt,
                        metrics=item.get("metrics"),
                        description=item.get("description"),
                        is_active=(p_id == active_id)
                    )
                    db.add(entry)
    
    # 2. Experience Store
    if os.path.exists(EXPERIENCE_FILE):
        with open(EXPERIENCE_FILE, "r") as f:
            try:
                data = json.load(f)
            except:
                data = {"by_key": {}}
            
            for key, items in data.get("by_key", {}).items():
                for it in items:
                    # Using batch_id and ingested_at as a weak uniqueness check
                    ingested_at = parse_iso(it.get("ingested_at"))
                    if not db.query(ExperienceEntry).filter_by(key=key, batch_id=it.get("batch_id"), ingested_at=ingested_at).first():
                        entry = ExperienceEntry(
                            key=key,
                            batch_id=it.get("batch_id"),
                            energy_kwh=it.get("energy_kwh"),
                            yield_pct=it.get("yield_pct"),
                            quality_deviation=it.get("quality_deviation"),
                            ingested_at=ingested_at or datetime.utcnow(),
                            anomaly_flag=it.get("anomaly_flag", False),
                            hash=it.get("hash"),
                            weights_at_time=it.get("weights_at_time"),
                            features=it.get("features")
                        )
                        db.add(entry)

    db.commit()
    db.close()
    print("Policy migration complete.")

if __name__ == "__main__":
    migrate()
