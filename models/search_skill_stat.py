from sqlalchemy import Column, Integer, ForeignKey, String, Date
from base import Base

class SearchSkillStat(Base):
    __tablename__ = "search_skill_stats"

    id = Column(Integer, primary_key=True, index=True)

    role_id = Column(Integer, ForeignKey("roles.id"))
    skill_id = Column(Integer, ForeignKey("skills.id"))

    type = Column(String(20))  # include | exclude

    count = Column(Integer, default=1)

    date = Column(Date)