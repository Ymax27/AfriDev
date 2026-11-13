"""Reputation ledger schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.schemas import ORMModel


class TransactionOut(ORMModel):
    id: UUID
    points: int
    action_type: str
    reference_type: str
    reference_id: str
    status: str
    note: str | None = None
    is_demo: bool
    created_at: datetime


class TransactionListOut(BaseModel):
    items: list[TransactionOut]
    total: int
    page: int
    page_size: int


class ReputationSummary(BaseModel):
    user_id: UUID
    username: str
    reputation_points: int
    level: str
    next_level: str | None = None
    points_to_next_level: int = 0
    recent_transactions: list[TransactionOut] = Field(default_factory=list)
