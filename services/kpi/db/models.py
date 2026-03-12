from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class KPIEntry(Base):
    __tablename__ = "kpi_entries"
    
    id = Column(Integer, primary_key=True)
    batch_id = Column(String, unique=True, index=True)
    energy_kwh = Column(Float)
    yield_pct = Column(Float)
    quality_deviation = Column(Boolean)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    anomaly_flag = Column(Boolean, default=False)
    anomaly_reasons = Column(JSON) # List of strings
    hash = Column(String)
