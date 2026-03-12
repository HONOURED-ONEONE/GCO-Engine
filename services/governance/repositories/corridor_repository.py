from typing import List, Optional
from sqlalchemy.orm import Session
from services.governance.db.models import CorridorVersion

class CorridorRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_active(self) -> Optional[CorridorVersion]:
        return self.db.query(CorridorVersion).filter_by(is_active=True).first()

    def get_version(self, version_tag: str) -> Optional[CorridorVersion]:
        return self.db.query(CorridorVersion).filter_by(version_tag=version_tag).first()

    def get_all(self) -> List[CorridorVersion]:
        return self.db.query(CorridorVersion).order_by(CorridorVersion.created_at.desc()).all()

    def add(self, version: CorridorVersion):
        # Ensure only one is active
        if version.is_active:
            self.db.query(CorridorVersion).update({CorridorVersion.is_active: False})
        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)
        return version

    def set_active(self, version_tag: str):
        self.db.query(CorridorVersion).update({CorridorVersion.is_active: False})
        version = self.get_version(version_tag)
        if version:
            version.is_active = True
            self.db.commit()
            self.db.refresh(version)
        return version
