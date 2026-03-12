from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class OTConfigEntry(Base):
    __tablename__ = "ot_config"
    
    id = Column(Integer, primary_key=True)
    config = Column(JSON)
    updated_at = Column(DateTime, default=datetime.utcnow)

class OTStateEntry(Base):
    __tablename__ = "ot_state"
    
    id = Column(Integer, primary_key=True)
    mode = Column(String) # shadow, guarded
    armed = Column(Boolean, default=False)
    last_write = Column(JSON)
    last_good_setpoint = Column(JSON)
    last_readback = Column(JSON)
    connector_state = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow)
