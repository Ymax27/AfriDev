"""Leaderboard endpoints."""

from fastapi import APIRouter, Query

from app.api.dependencies import DbSession
from app.modules.leaderboard import service
from app.modules.leaderboard.schemas import (
    CountryRankOut,
    DeveloperLeaderboardOut,
    ProjectRankOut,
)

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("/developers", response_model=DeveloperLeaderboardOut)
async def developer_leaderboard(
    db: DbSession,
    period: str = Query(default="all", pattern="^(all|week|month)$"),
    country: str | None = Query(default=None, min_length=2, max_length=2),
    limit: int = Query(default=20, ge=1, le=100),
    include_demo: bool | None = Query(default=None),
) -> DeveloperLeaderboardOut:
    include = service.demo_default() if include_demo is None else include_demo
    items = await service.developer_leaderboard(
        db, period=period, country_code=country, limit=limit, include_demo=include
    )
    return DeveloperLeaderboardOut(
        items=items, scope="country" if country else "global", period=period, country=country
    )


@router.get("/projects", response_model=list[ProjectRankOut])
async def project_leaderboard(
    db: DbSession,
    limit: int = Query(default=20, ge=1, le=100),
    country: str | None = Query(default=None, min_length=2, max_length=2),
    include_demo: bool | None = Query(default=None),
) -> list[ProjectRankOut]:
    include = service.demo_default() if include_demo is None else include_demo
    return await service.project_leaderboard(db, limit=limit, include_demo=include, country_code=country)


@router.get("/countries", response_model=list[CountryRankOut])
async def country_leaderboard(
    db: DbSession,
    limit: int = Query(default=20, ge=1, le=100),
    period: str = Query(default="week", pattern="^(week|month|all)$"),
    include_demo: bool | None = Query(default=None),
) -> list[CountryRankOut]:
    include = service.demo_default() if include_demo is None else include_demo
    return await service.country_leaderboard(db, limit=limit, include_demo=include, period=period)
