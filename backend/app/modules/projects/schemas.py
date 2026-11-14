"""Project schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.enums import CollaborationMode
from app.core.schemas import CountryOut, ORMModel, UserSummary


class ProjectCreate(BaseModel):
    name: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=20, max_length=5000)
    repository_url: str | None = Field(default=None, max_length=500)
    demo_url: str | None = Field(default=None, max_length=500)
    cover_image_url: str | None = Field(default=None, max_length=500)
    technologies: list[str] = Field(default_factory=list, max_length=15)
    tags: list[str] = Field(default_factory=list, max_length=10)
    category: str = Field(default="web", max_length=60)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    collaboration_mode: CollaborationMode = CollaborationMode.SHOWCASE

    @field_validator("repository_url", "demo_url", "cover_image_url")
    @classmethod
    def _validate_url(cls, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        if not value.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return value


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(default=None, min_length=20, max_length=5000)
    repository_url: str | None = None
    demo_url: str | None = None
    cover_image_url: str | None = None
    technologies: list[str] | None = None
    tags: list[str] | None = None
    category: str | None = None
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    collaboration_mode: CollaborationMode | None = None
    is_published: bool | None = None


class ProjectOut(ORMModel):
    id: UUID
    name: str
    slug: str
    description: str
    repository_url: str | None = None
    demo_url: str | None = None
    cover_image_url: str | None = None
    technologies: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    category: str
    collaboration_mode: str
    ownership_status: str
    is_published: bool
    is_demo: bool
    is_featured: bool
    view_count: int
    github_stars: int
    creator: UserSummary
    country: CountryOut | None = None
    created_at: datetime
    likes_count: int = 0
    contributions_count: int = 0
    feedback_count: int = 0
    liked_by_me: bool = False
    passed_by_me: bool = False


class ProjectListOut(BaseModel):
    items: list[ProjectOut]
    total: int
    page: int
    page_size: int


class FeedbackCreate(BaseModel):
    concept_answer: str = Field(min_length=5, max_length=1000)
    improvement_answer: str = Field(min_length=5, max_length=1000)
    feature_answer: str = Field(min_length=5, max_length=1000)


class FeedbackOut(ORMModel):
    id: UUID
    project_id: UUID
    concept_answer: str
    improvement_answer: str
    feature_answer: str
    is_useful: bool
    author: UserSummary
    created_at: datetime


class OwnershipVerifyRequest(BaseModel):
    method: str = Field(default="repository_file", pattern="^(repository_file|repository_owner|domain)$")


class OwnershipConfirmRequest(BaseModel):
    token: str | None = Field(default=None, max_length=200)


class OwnershipVerificationOut(ORMModel):
    id: UUID
    project_id: UUID
    method: str
    status: str
    challenge_token: str
    created_at: datetime
    verified_at: datetime | None = None
