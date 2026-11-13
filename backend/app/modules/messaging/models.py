"""Private and contextual conversations with persisted messages."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.core.enums import ConversationType


class Conversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "conversations"

    type: Mapped[str] = mapped_column(String(30), default=ConversationType.CONTRIBUTION.value, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    project_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    contribution_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("contribution_requests.id", ondelete="SET NULL"), unique=True
    )
    country_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("countries.id", ondelete="CASCADE"))
    mission_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("missions.id", ondelete="CASCADE"))
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    members = relationship("ConversationMember", lazy="selectin", cascade="all, delete-orphan")


class ConversationMember(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "conversation_members"
    __table_args__ = (
        UniqueConstraint("conversation_id", "user_id", name="uq_conversation_members_conversation_user"),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20), default="member", nullable=False)
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Message(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_conversation_created", "conversation_id", "created_at"),)

    conversation_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    sender_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    sender = relationship("User", lazy="selectin")
