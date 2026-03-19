from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, Float, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from base import Base

job_skills = Table(
    "job_skills",
    Base.metadata,
    Column("job_id", Integer, ForeignKey("jobs.id")),
    Column("skill_id", Integer, ForeignKey("skills.id"))
)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    job_hash = Column(String(255), unique=True, index=True)
    external_id = Column(String(255), nullable=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    company_id = Column(Integer, ForeignKey("companies.id"))
    title = Column(String(255))
    location = Column(String(255))
    is_remote = Column(Boolean)
    job_url = Column(Text)
    match_percentage = Column(Float, default=0)
    posted_at = Column(DateTime, nullable=True)
    collected_at = Column(DateTime, server_default=func.now())
    