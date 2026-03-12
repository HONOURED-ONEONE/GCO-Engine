import json
import os
import sys
from datetime import datetime

# Add root to sys.path
sys.path.append(os.getcwd())

from services.governance.db.session import SessionLocal, init_db
from services.governance.db.models import CorridorVersion, Proposal, AuditLog, ModeState

DATA_DIR = "./data"
CORRIDOR_FILE = os.path.join(DATA_DIR, "corridor.json")
REGISTRY_FILE = os.path.join(DATA_DIR, "version_registry.json")

def parse_iso(dt_str):
    if not dt_str: return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except:
        return datetime.utcnow()

def migrate():
    print("Migrating Governance data...")
    init_db()
    db = SessionLocal()
    
    # 1. Migrate Corridor Versions
    if os.path.exists(CORRIDOR_FILE):
        with open(CORRIDOR_FILE, "r") as f:
            data = json.load(f)
            active_v = data.get("active_version")
            for v_tag, v_data in data.get("versions", {}).items():
                if not db.query(CorridorVersion).filter_by(version_tag=v_tag).first():
                    cv = CorridorVersion(
                        version_tag=v_tag,
                        bounds=v_data.get("bounds"),
                        created_at=parse_iso(v_data.get("created_at")),
                        evidence=v_data.get("evidence"),
                        is_active=(v_tag == active_v)
                    )
                    db.add(cv)
    
    # 2. Migrate Registry (Proposals, Audit, Mode)
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f:
            data = json.load(f)
            
            # Proposals
            for p_data in data.get("proposals", []):
                if not db.query(Proposal).filter_by(proposal_id=p_data.get("id")).first():
                    p = Proposal(
                        proposal_id=p_data.get("id"),
                        delta=p_data.get("delta"),
                        evidence=p_data.get("evidence"),
                        status=p_data.get("status"),
                        created_at=parse_iso(p_data.get("created_at")),
                        created_by=p_data.get("created_by"),
                        decided_at=parse_iso(p_data.get("decided_at")),
                        decided_by=p_data.get("decided_by"),
                        notes=p_data.get("notes")
                    )
                    db.add(p)
            
            # Audit
            for a_data in data.get("audit", []):
                # Using timestamp and type for a simple uniqueness check
                if not db.query(AuditLog).filter_by(at=parse_iso(a_data.get("at")), type=a_data.get("type")).first():
                    al = AuditLog(
                        at=parse_iso(a_data.get("at")),
                        type=a_data.get("type"),
                        data=a_data.get("data"),
                        user_id=a_data.get("user_id"),
                        hash=a_data.get("hash")
                    )
                    db.add(al)
            
            # Mode State
            if "last_mode" in data:
                if not db.query(ModeState).first():
                    ms = ModeState(
                        mode=data.get("last_mode"),
                        weights=data.get("last_mode_weights"),
                        changed_at=parse_iso(data.get("last_mode_changed_at")),
                        operator_id=data.get("last_operator_id")
                    )
                    db.add(ms)

    db.commit()
    db.close()
    print("Governance migration complete.")

if __name__ == "__main__":
    migrate()
