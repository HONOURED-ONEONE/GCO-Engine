from typing import List, Optional
from sqlalchemy.orm import Session
from services.governance.db.models import Proposal

class ProposalRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, proposal_id: str) -> Optional[Proposal]:
        return self.db.query(Proposal).filter_by(proposal_id=proposal_id).first()

    def get_all(self, status: Optional[str] = None) -> List[Proposal]:
        query = self.db.query(Proposal)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Proposal.created_at.desc()).all()

    def add(self, proposal: Proposal):
        self.db.add(proposal)
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def update(self, proposal: Proposal):
        self.db.commit()
        self.db.refresh(proposal)
        return proposal

    def count(self):
        return self.db.query(Proposal).count()
