from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from database import Base

class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id = Column(Integer, primary_key=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    total_jobs = Column(Integer)


class MarketSnapshotSkill(Base):
    __tablename__ = "market_snapshot_skills"

    snapshot_id = Column(Integer, ForeignKey("market_snapshots.id"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), primary_key=True)

    frequency = Column(Integer)