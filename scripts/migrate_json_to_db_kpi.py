import json
import os
import sys
from datetime import datetime

# Add root to sys.path
sys.path.append(os.getcwd())

from services.kpi.db.session import SessionLocal, init_db
from services.kpi.db.models import KPIEntry

DATA_DIR = "./data"
KPI_STORE_FILE = os.path.join(DATA_DIR, "kpi_store.json")

def parse_iso(dt_str):
    if not dt_str: return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except:
        return datetime.utcnow()

def migrate():
    print("Migrating KPI data...")
    init_db()
    db = SessionLocal()
    
    if os.path.exists(KPI_STORE_FILE):
        with open(KPI_STORE_FILE, "r") as f:
            try:
                data = json.load(f)
            except:
                data = {"items": []}
                
            for item in data.get("items", []):
                if not db.query(KPIEntry).filter_by(batch_id=item.get("batch_id")).first():
                    entry = KPIEntry(
                        batch_id=item.get("batch_id"),
                        energy_kwh=item.get("energy_kwh"),
                        yield_pct=item.get("yield_pct"),
                        quality_deviation=item.get("quality_deviation"),
                        ingested_at=parse_iso(item.get("ingested_at")),
                        updated_at=parse_iso(item.get("updated_at")),
                        anomaly_flag=item.get("anomaly_flag", False),
                        anomaly_reasons=item.get("anomaly_reasons", []),
                        hash=item.get("hash")
                    )
                    db.add(entry)

    db.commit()
    db.close()
    print("KPI migration complete.")

if __name__ == "__main__":
    migrate()
