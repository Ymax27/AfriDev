"""User and profile schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.schemas import CountryOut, ORMModel, SkillOut


class RoleOut(ORMModel):
    role: str


class UserOut(ORMModel):
    id: UUID
    username: str
    full_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    city: str | None = None
    website_url: str | None = None
    github_url: str | None = None
    github_login: str | None = None
    country: CountryOut | None = None
    reputation_points: int
    level: str
    is_admin: bool
    is_demo: bool
    roles: list[RoleOut] = Field(default_factory=list)
    skills: list[SkillOut] = Field(default_factory=list)
    created_at: datetime


class UserProfileOut(UserOut):
    projects_count: int = 0
    accepted_solutions_count: int = 0
    field_reports_count: int = 0
    verified_projects_count: int = 0
    merged_contributions_count: int = 0
    titles: list[str] = Field(default_factory=list)


class ProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    bio: str | None = Field(default=None, max_length=2000)
    city: str | None = Field(default=None, max_length=120)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    website_url: str | None = Field(default=None, max_length=500)
    github_url: str | None = Field(default=None, max_length=500)
    skills: list[str] | None = Field(default=None, max_length=20)
    roles: list[str] | None = None

    @field_validator("website_url", "github_url")
    @classmethod
    def _validate_url(cls, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        if not value.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return value


class UserListResponse(BaseModel):
    items: list[UserOut]
    total: int
    page: int
    page_size: int
