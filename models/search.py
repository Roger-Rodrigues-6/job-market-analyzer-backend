from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime

from base import Base


class Search(Base):
    """Parâmetros enviados pelo formulário do front para a raspagem (snapshot por requisição).

    Include/exclude de skills e empresas ficam nas tabelas `search_skills` e `search_excluded_companies`.
    """

    __tablename__ = "searches"

    id = Column(Integer, primary_key=True, index=True)

    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False, index=True)

    query = Column(String(500), default="")

    location = Column(String(255), default="")
    remote = Column(String(50), default="")
    period = Column(String(50), default="24h")
    english = Column(String(50), default="include")

    filters_hash = Column(String(255), index=True)

    ip = Column(String(100), default="")
    user_agent = Column(String(255), default="")

    created_at = Column(DateTime, default=datetime.utcnow)
