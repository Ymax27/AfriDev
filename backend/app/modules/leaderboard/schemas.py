"""Leaderboard schemas."""

from uuid import UUID

from pydantic import BaseModel

from app.core.schemas import CountryOut


class DeveloperRankOut(BaseModel):
    rank: int
    user_id: UUID
    username: str
    full_name: str | None = None
    avatar_url: str | None = None
    country: CountryOut | None = None
    level: str
    reputation_points: int
    period_points: int


class ProjectRankOut(BaseModel):
    rank: int
    project_id: UUID
    name: str
    slug: str
    creator_username: str
    country: CountryOut | None = None
    likes: int
    accepted_contributors: int
    useful_feedback: int
    visits: int
    score: float


class CountryRankOut(BaseModel):
    rank: int
    country: CountryOut
    active_developers: int
    total_points: int
    week_points: int = 0
    average_points: float
    period: str = "week"


class DeveloperLeaderboardOut(BaseModel):
    items: list[DeveloperRankOut]
    scope: str
    period: str
    country: str | None = None
