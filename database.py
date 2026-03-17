from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base

import os
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from models.company import Company
from models.job import Job
from models.skill import Skill
from models.job_skill import JobSkill
from models.market_snapshot import MarketSnapshot, MarketSnapshotSkill


def init_db():
    Base.metadata.create_all(bind=engine)