"""Notification schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.core.schemas import ORMModel


class NotificationOut(ORMModel):
    id: UUID
    type: str
    title: str
    body: str | None = None
    link: str | None = None
    is_read: bool
    created_at: datetime


class NotificationListOut(BaseModel):
    items: list[NotificationOut]
    total: int
    page: int
    page_size: int
    unread_count: int = 0
