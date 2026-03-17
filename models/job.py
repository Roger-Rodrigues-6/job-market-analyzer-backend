from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from base import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(255), unique=True, nullable=False)

    title = Column(String(255))
    company_id = Column(Integer, ForeignKey("companies.id"))

    location = Column(String(255))
    is_remote = Column(Boolean)

    job_url = Column(Text)

    posted_at = Column(DateTime)
    collected_at = Column(TIMESTAMP, server_default=func.now())