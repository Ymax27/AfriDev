"""Contribution request schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.enums import ContributionDomain
from app.core.schemas import ORMModel, UserSummary


class ContributionCreate(BaseModel):
    message: str = Field(min_length=20, max_length=600, description="Two to three lines about your offer")
    domain: ContributionDomain


class ContributionOut(ORMModel):
    id: UUID
    project_id: UUID
    message: str
    domain: str
    status: str
    requester: UserSummary
    conversation_id: UUID | None = None
    created_at: datetime
    reviewed_at: datetime | None = None
    merged_at: datetime | None = None


class ContributionListOut(BaseModel):
    items: list[ContributionOut]
    total: int
    page: int
    page_size: int
