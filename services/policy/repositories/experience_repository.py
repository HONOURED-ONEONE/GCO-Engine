from typing import List, Optional
from sqlalchemy.orm import Session
from services.policy.db.models import ExperienceEntry

class ExperienceRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, entry: ExperienceEntry):
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_by_key(self, key: str, limit: int = 100) -> List[ExperienceEntry]:
        return self.db.query(ExperienceEntry).filter_by(key=key).order_by(ExperienceEntry.ingested_at.desc()).limit(limit).all()

    def count_by_key(self, key: str) -> int:
        return self.db.query(ExperienceEntry).filter_by(key=key).count()

    def total_count(self) -> int:
        return self.db.query(ExperienceEntry).count()
