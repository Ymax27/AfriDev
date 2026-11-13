"""Country hub schemas."""

from uuid import UUID

from pydantic import BaseModel, Field

from app.core.schemas import CountryOut, ORMModel


class CountryStats(BaseModel):
    developers: int = 0
    projects: int = 0
    field_reports: int = 0
    accepted_contributions: int = 0
    reputation_points: int = 0
    activity_score: int = 0


class CountryHubOut(BaseModel):
    country: CountryOut
    stats: CountryStats
    top_developers: list[dict] = Field(default_factory=list)
    recent_projects: list[dict] = Field(default_factory=list)
    recent_field_reports: list[dict] = Field(default_factory=list)
    open_missions: list[dict] = Field(default_factory=list)
    rank: int | None = None


class LeaderboardCountryOut(ORMModel):
    id: UUID
    code: str
    name: str
    name_fr: str
    flag_emoji: str | None = None
