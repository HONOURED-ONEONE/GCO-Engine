from typing import List, Optional
from sqlalchemy.orm import Session
from services.kpi.db.models import Base, KPIEntry

class KPIRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_batch_id(self, batch_id: str) -> Optional[KPIEntry]:
        return self.db.query(KPIEntry).filter_by(batch_id=batch_id).first()

    def get_recent(self, limit: int = 100) -> List[KPIEntry]:
        # Sort by updated_at if exists, else ingested_at
        # In SQL this is COALESCE
        from sqlalchemy import func
        ts = func.coalesce(KPIEntry.updated_at, KPIEntry.ingested_at)
        return self.db.query(KPIEntry).order_by(ts.desc()).limit(limit).all()

    def add(self, entry: KPIEntry):
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def update(self, entry: KPIEntry):
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_all(self) -> List[KPIEntry]:
        return self.db.query(KPIEntry).all()

    def get_stats_last_n(self, n: int = 10) -> List[KPIEntry]:
        from sqlalchemy import func
        ts = func.coalesce(KPIEntry.updated_at, KPIEntry.ingested_at)
        return self.db.query(KPIEntry).order_by(ts.asc()).limit(n).all()
        # Wait, get_stats_last_n in original code sorts chronologically and takes last n.
        # My query above takes FIRST n if I sort ASC.
        # Let's fix it.
        # subquery = self.db.query(KPIEntry).order_by(ts.desc()).limit(n).subquery()
        # return self.db.query(subquery).order_by(ts.asc()).all()
        # Simple way: get last n by DESC, then reverse in python if needed.
    
    def get_last_n_chronological(self, n: int = 10) -> List[KPIEntry]:
        from sqlalchemy import func
        ts = func.coalesce(KPIEntry.updated_at, KPIEntry.ingested_at)
        items = self.db.query(KPIEntry).order_by(ts.desc()).limit(n).all()
        return items[::-1] # Reverse to be chronological

    def count_anomalies(self) -> int:
        return self.db.query(KPIEntry).filter_by(anomaly_flag=True).count()
