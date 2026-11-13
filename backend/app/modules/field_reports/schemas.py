"""Field report schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.schemas import CountryOut, ORMModel, UserSummary


class FieldReportOut(ORMModel):
    id: UUID
    title: str
    problem_summary: str
    solution_summary: str
    common_errors: str | None = None
    workarounds: str | None = None
    status: str
    confirmation_count: int
    last_validated_at: datetime | None = None
    problem_id: UUID | None = None
    solution_id: UUID | None = None
    api_entry_id: UUID | None = None
    author: UserSummary
    country: CountryOut | None = None
    is_demo: bool
    created_at: datetime


class FieldReportListOut(BaseModel):
    items: list[FieldReportOut]
    total: int
    page: int
    page_size: int


class FieldReportUpdate(BaseModel):
    common_errors: str | None = Field(default=None, max_length=4000)
    workarounds: str | None = Field(default=None, max_length=4000)
    solution_summary: str | None = Field(default=None, min_length=20, max_length=5000)


class ConfirmationCreate(BaseModel):
    comment: str | None = Field(default=None, max_length=500)


class ConfirmationOut(ORMModel):
    id: UUID
    report_id: UUID
    user_id: UUID
    comment: str | None = None
    created_at: datetime
