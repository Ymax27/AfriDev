"""Moderation schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.schemas import ORMModel


class ReportCreate(BaseModel):
    target_type: str = Field(pattern="^(project|problem|solution|field_report|message|user|mission)$")
    target_id: str = Field(min_length=1, max_length=64)
    reason: str = Field(min_length=3, max_length=60)
    details: str | None = Field(default=None, max_length=2000)


class ReportOut(ORMModel):
    id: UUID
    reporter_id: UUID
    target_type: str
    target_id: str
    reason: str
    details: str | None = None
    status: str
    resolution_note: str | None = None
    created_at: datetime


class BlockCreate(BaseModel):
    username: str = Field(min_length=3, max_length=40)
    reason: str | None = Field(default=None, max_length=255)


class BlockOut(BaseModel):
    id: UUID
    blocked_id: UUID
    blocked_username: str
    reason: str | None = None
    created_at: datetime


class ReportResolve(BaseModel):
    status: str = Field(pattern="^(resolved|dismissed)$")
    resolution_note: str | None = Field(default=None, max_length=1000)
