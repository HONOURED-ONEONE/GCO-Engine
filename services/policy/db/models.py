from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class PolicyEntry(Base):
    __tablename__ = "policy_registry"
    
    id = Column(Integer, primary_key=True)
    policy_id = Column(String, unique=True, index=True)
    hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    metrics = Column(JSON) # e.g. {"energy_improvement_pct": 3.2, ...}
    description = Column(String)
    is_active = Column(Boolean, default=False)

class ExperienceEntry(Base):
    __tablename__ = "experience_store"
    
    id = Column(Integer, primary_key=True)
    key = Column(String, index=True) # e.g. "corridor"
    batch_id = Column(String)
    energy_kwh = Column(Float)
    yield_pct = Column(Float)
    quality_deviation = Column(Boolean)
    ingested_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    anomaly_flag = Column(Boolean, default=False)
    anomaly_reasons = Column(JSON)
    hash = Column(String)
    weights_at_time = Column(JSON)
    features = Column(JSON)
    metadata_json = Column(JSON)
