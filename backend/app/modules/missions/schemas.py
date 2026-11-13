"""Mission schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.enums import MissionStatus
from app.core.schemas import CountryOut, ORMModel, UserSummary


class MissionCreate(BaseModel):
    title: str = Field(min_length=8, max_length=200)
    description: str = Field(min_length=30, max_length=8000)
    objectives: str = Field(min_length=20, max_length=8000)
    required_skills: list[str] = Field(default_factory=list, max_length=15)
    api_entry_id: UUID | None = None
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    deadline: datetime | None = None
    reward_points: int = Field(default=30, ge=0, le=500)
    reward_description: str | None = Field(default=None, max_length=255)
    status: MissionStatus = MissionStatus.PUBLISHED


class MissionOut(ORMModel):
    id: UUID
    title: str
    slug: str
    description: str
    objectives: str
    required_skills: list[str] = Field(default_factory=list)
    reward_points: int
    reward_description: str | None = None
    deadline: datetime | None = None
    status: str
    sponsor: UserSummary
    country: CountryOut | None = None
    api_entry_id: UUID | None = None
    is_demo: bool
    created_at: datetime
    submissions_count: int = 0


class MissionListOut(BaseModel):
    items: list[MissionOut]
    total: int
    page: int
    page_size: int


class SubmissionCreate(BaseModel):
    summary: str = Field(min_length=30, max_length=4000)
    solution_url: str | None = Field(default=None, max_length=500)


class SubmissionReview(BaseModel):
    approve: bool
    review_note: str | None = Field(default=None, max_length=1000)


class SubmissionOut(ORMModel):
    id: UUID
    mission_id: UUID
    developer_id: UUID
    summary: str
    solution_url: str | None = None
    status: str
    review_note: str | None = None
    points_awarded: int
    created_at: datetime
