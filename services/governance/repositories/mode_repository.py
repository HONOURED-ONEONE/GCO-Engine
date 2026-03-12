from typing import Optional
from sqlalchemy.orm import Session
from services.governance.db.models import ModeState

class ModeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_current(self) -> Optional[ModeState]:
        return self.db.query(ModeState).order_by(ModeState.changed_at.desc()).first()

    def add(self, state: ModeState):
        self.db.add(state)
        self.db.commit()
        self.db.refresh(state)
        return state
