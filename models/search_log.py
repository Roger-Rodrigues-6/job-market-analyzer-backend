from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from base import Base

class SearchLog(Base):
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)

    role_id = Column(Integer, ForeignKey("roles.id"))

    filters_hash = Column(String(255), index=True)

    ip = Column(String(100))
    user_agent = Column(String(255))

    created_at = Column(DateTime, default=datetime.utcnow)