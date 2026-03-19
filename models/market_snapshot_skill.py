from sqlalchemy import Column, Integer, ForeignKey
from base import Base

class MarketSnapshotSkill(Base):
    __tablename__ = "market_snapshot_skills"

    id = Column(Integer, primary_key=True, index=True)

    snapshot_id = Column(Integer, ForeignKey("market_snapshots.id"))
    skill_id = Column(Integer, ForeignKey("skills.id"))

    count = Column(Integer)