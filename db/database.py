from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Render에서는 데이터가 사라질 수 있으므로, 나중에는 PostgreSQL 사용을 권장합니다.
DB_URL = os.getenv("DATABASE_URL", "sqlite:///data/akari.db")

engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if "sqlite" in DB_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()