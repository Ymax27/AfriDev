"""Shared Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CountryOut(ORMModel):
    id: UUID
    code: str
    name: str
    name_fr: str
    flag_emoji: str | None = None
    region: str | None = None


class UserSummary(ORMModel):
    id: UUID
    username: str
    full_name: str | None = None
    avatar_url: str | None = None
    level: str
    reputation_points: int
    country: CountryOut | None = None


class SkillOut(ORMModel):
    id: UUID
    name: str
    level: str
    years_experience: int | None = None


class MessageOut(BaseModel):
    message: str = "ok"


class PaginatedResponse(BaseModel):
    items: list[BaseModel]
    total: int
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class TimestampedOut(ORMModel):
    id: UUID
    created_at: datetime
