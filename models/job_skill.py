from sqlalchemy import Column, Integer, ForeignKey
from database import Base

class JobSkill(Base):
    __tablename__ = "job_skills"

    job_id = Column(Integer, ForeignKey("jobs.id"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), primary_key=True)

    match_count = Column(Integer, default=1)