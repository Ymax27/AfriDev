"""Immutable reputation transaction ledger."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.core.enums import ReputationStatus


class ReputationTransaction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Append-only ledger: the source of truth for every reputation point."""

    __tablename__ = "reputation_transactions"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "action_type", "reference_type", "reference_id", name="uq_reputation_transactions_action"
        ),
        Index("ix_reputation_transactions_user_created", "user_id", "created_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    reference_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=ReputationStatus.APPROVED.value, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
