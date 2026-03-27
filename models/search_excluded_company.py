from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint

from base import Base


class SearchExcludedCompany(Base):
    """Empresas excluídas no filtro da busca (N:N com `searches` e `companies`)."""

    __tablename__ = "search_excluded_companies"
    __table_args__ = (
        UniqueConstraint("search_id", "company_id", name="uq_search_excluded_company"),
    )

    id = Column(Integer, primary_key=True, index=True)

    search_id = Column(Integer, ForeignKey("searches.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
