from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint

from base import Base


class SearchSkillLink(Base):
    """Ligação N:N entre uma busca (`searches`) e skills (include ou exclude)."""

    __tablename__ = "search_skills"
    __table_args__ = (
        UniqueConstraint("search_id", "skill_id", "kind", name="uq_search_skill_kind"),
    )

    id = Column(Integer, primary_key=True, index=True)

    search_id = Column(Integer, ForeignKey("searches.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False, index=True)
    kind = Column(String(10), nullable=False)  # include | exclude
