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
DB_PORT = os.getenv("DB_PORT", "3306")

if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
    raise ValueError("❌ Variáveis de ambiente do banco não estão definidas corretamente")

DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    "?charset=utf8mb4"
)

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

from models.skill import Skill
from models.role import Role
from models.market_snapshot import MarketSnapshot
from models.market_snapshot_skill import MarketSnapshotSkill
from models.search_skill_stat import SearchSkillStat
from models.search_log import SearchLog
from models.job import Job

def init_db():
    Base.metadata.create_all(bind=engine)