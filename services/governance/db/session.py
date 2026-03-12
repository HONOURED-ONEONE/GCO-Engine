import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from services.governance.db.models import Base

# Default to SQLite for local development
DATABASE_URL = os.getenv("GOVERNANCE_DB_URL", "sqlite:///./governance.db")
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "database") # database or file

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    if STORAGE_BACKEND == "database":
        Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def is_db_enabled():
    return STORAGE_BACKEND == "database"
