"""Terrain knowledge: problems and their proposed solutions."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class KnowledgeProblem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "knowledge_problems"
    __table_args__ = (Index("ix_knowledge_problems_country_category", "country_id", "category"),)

    author_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    country_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("countries.id", ondelete="SET NULL"))
    api_entry_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("api_entries.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    technology: Mapped[str | None] = mapped_column(String(80))
    code_snippet: Mapped[str | None] = mapped_column(Text)
    documentation_links: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    author = relationship("User", lazy="selectin")
    country = relationship("Country", lazy="selectin")


class Solution(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "solutions"

    problem_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("knowledge_problems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    code_snippet: Mapped[str | None] = mapped_column(Text)
    implementation_steps: Mapped[str | None] = mapped_column(Text)
    references: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    is_accepted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    author = relationship("User", lazy="selectin")


class SolutionVote(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Community usefulness vote: +2 points to the solution author, capped per solution."""

    __tablename__ = "solution_votes"
    __table_args__ = (UniqueConstraint("solution_id", "voter_id", name="uq_solution_votes_solution_voter"),)

    solution_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("solutions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    voter_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
