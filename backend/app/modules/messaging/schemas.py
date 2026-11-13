"""Messaging schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.schemas import ORMModel


class MemberOut(ORMModel):
    user_id: UUID
    role: str


class ConversationOut(ORMModel):
    id: UUID
    type: str
    title: str
    project_id: UUID | None = None
    country_id: UUID | None = None
    mission_id: UUID | None = None
    last_message_at: datetime | None = None
    created_at: datetime
    members: list[MemberOut] = Field(default_factory=list)


class ConversationListOut(BaseModel):
    items: list[ConversationOut]
    total: int
    page: int
    page_size: int


class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class MessageOut(ORMModel):
    id: UUID
    conversation_id: UUID
    sender_id: UUID
    body: str
    created_at: datetime
