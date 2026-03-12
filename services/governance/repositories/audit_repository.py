from typing import List, Optional
from sqlalchemy.orm import Session
from services.governance.db.models import AuditLog

class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, log: AuditLog):
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_recent(self, limit: int = 100) -> List[AuditLog]:
        return self.db.query(AuditLog).order_by(AuditLog.at.desc()).limit(limit).all()
