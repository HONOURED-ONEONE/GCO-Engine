from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class CorridorVersion(Base):
    __tablename__ = "corridor_versions"
    
    id = Column(Integer, primary_key=True)
    version_tag = Column(String, unique=True, index=True)
    bounds = Column(JSON) # e.g. {"temperature": {"lower": 145.0, "upper": 155.0}, ...}
    created_at = Column(DateTime, default=datetime.utcnow)
    evidence = Column(String)
    is_active = Column(Boolean, default=False)

class Proposal(Base):
    __tablename__ = "proposals"
    
    id = Column(Integer, primary_key=True)
    proposal_id = Column(String, unique=True, index=True) # e.g. prop-0001
    delta = Column(JSON)
    evidence = Column(JSON)
    status = Column(String, default="pending") # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)
    decided_at = Column(DateTime, nullable=True)
    decided_by = Column(String, nullable=True)
    notes = Column(String, nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    at = Column(DateTime, default=datetime.utcnow)
    type = Column(String)
    data = Column(JSON)
    user_id = Column(String)
    hash = Column(String)

class ModeState(Base):
    __tablename__ = "mode_states"
    
    id = Column(Integer, primary_key=True)
    mode = Column(String)
    weights = Column(JSON)
    changed_at = Column(DateTime, default=datetime.utcnow)
    operator_id = Column(String)
