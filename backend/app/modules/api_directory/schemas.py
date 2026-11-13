"""API directory schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.schemas import ORMModel


class APIEntryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    provider_name: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=20, max_length=4000)
    category: str = Field(min_length=2, max_length=60)
    countries: list[str] = Field(default_factory=list, max_length=60)
    documentation_url: str = Field(min_length=10, max_length=500)
    pricing: str | None = Field(default=None, max_length=255)
    api_status: str = Field(default="operational", max_length=30)
    integration_notes: str | None = Field(default=None, max_length=4000)


class APIEntryOut(ORMModel):
    id: UUID
    name: str
    provider_name: str
    slug: str
    description: str
    category: str
    countries: list[str] = Field(default_factory=list)
    documentation_url: str
    pricing: str | None = None
    api_status: str
    integration_notes: str | None = None
    is_published: bool
    is_demo: bool
    created_at: datetime
    related_field_reports: int = 0


class APIEntryListOut(BaseModel):
    items: list[APIEntryOut]
    total: int
    page: int
    page_size: int


class APICategoryOut(BaseModel):
    category: str
    count: int
