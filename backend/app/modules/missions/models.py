"""Sponsored missions and developer submissions."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.core.enums import MissionStatus


class Mission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "missions"
    __table_args__ = (Index("ix_missions_status_deadline", "status", "deadline"),)

    sponsor_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    api_entry_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("api_entries.id", ondelete="SET NULL"))
    country_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("countries.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    objectives: Mapped[str] = mapped_column(Text, nullable=False)
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    reward_points: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    reward_description: Mapped[str | None] = mapped_column(String(255))
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), default=MissionStatus.PUBLISHED.value, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    sponsor = relationship("User", lazy="selectin")
    country = relationship("Country", lazy="selectin")


class MissionSubmission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "mission_submissions"
    __table_args__ = (
        Index("ix_mission_submissions_mission_status", "mission_id", "status"),
    )

    mission_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False
    )
    developer_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    solution_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), default="submitted", nullable=False)
    review_note: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    points_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
