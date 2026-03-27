from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from datetime import datetime
from base import Base

class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id = Column(Integer, primary_key=True, index=True)

    role_id = Column(Integer, ForeignKey("roles.id"))
    location = Column(String(255))
    remote = Column(String(50))
    period = Column(String(50))

    total_jobs = Column(Integer)

    # Dia civil (UTC) ao qual o snapshot se refere; usado pelo job diário D−1
    report_date = Column(Date, nullable=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)