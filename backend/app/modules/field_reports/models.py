"""Field reports derived from accepted solutions, plus country confirmations."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.core.enums import ReportStatus


class FieldReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "field_reports"
    __table_args__ = (Index("ix_field_reports_country_status", "country_id", "status"),)

    problem_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("knowledge_problems.id", ondelete="SET NULL"), index=True
    )
    solution_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("solutions.id", ondelete="SET NULL"), unique=True
    )
    author_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    country_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("countries.id", ondelete="SET NULL"))
    api_entry_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("api_entries.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    problem_summary: Mapped[str] = mapped_column(Text, nullable=False)
    solution_summary: Mapped[str] = mapped_column(Text, nullable=False)
    common_errors: Mapped[str | None] = mapped_column(Text)
    workarounds: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default=ReportStatus.PUBLISHED.value, nullable=False, index=True)
    confirmation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    author = relationship("User", lazy="selectin")
    country = relationship("Country", lazy="selectin")


class FieldReportConfirmation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "field_report_confirmations"
    __table_args__ = (UniqueConstraint("report_id", "user_id", name="uq_field_report_confirmations_report_user"),)

    report_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("field_reports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    country_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("countries.id", ondelete="SET NULL"))
    comment: Mapped[str | None] = mapped_column(Text)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
