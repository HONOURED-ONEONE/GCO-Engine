from typing import List, Optional
from sqlalchemy.orm import Session
from services.policy.db.models import PolicyEntry

class PolicyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, policy_id: str) -> Optional[PolicyEntry]:
        return self.db.query(PolicyEntry).filter_by(policy_id=policy_id).first()

    def get_active(self) -> Optional[PolicyEntry]:
        return self.db.query(PolicyEntry).filter_by(is_active=True).first()

    def get_all(self) -> List[PolicyEntry]:
        return self.db.query(PolicyEntry).order_by(PolicyEntry.created_at.desc()).all()

    def add_or_update(self, policy_id: str, data: dict):
        existing = self.get_by_id(policy_id)
        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
        else:
            entry = PolicyEntry(
                policy_id=policy_id,
                hash=data.get("hash"),
                created_at=data.get("created_at"),
                metrics=data.get("metrics"),
                description=data.get("description"),
                is_active=data.get("is_active", False)
            )
            self.db.add(entry)
        self.db.commit()

    def set_active(self, policy_id: str):
        self.db.query(PolicyEntry).update({PolicyEntry.is_active: False})
        existing = self.get_by_id(policy_id)
        if existing:
            existing.is_active = True
        self.db.commit()
