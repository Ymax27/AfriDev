"""Developer, project and country rankings."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import ReputationStatus
from app.core.schemas import CountryOut
from app.modules.contributions.models import ContributionRequest
from app.modules.countries.models import Country
from app.modules.leaderboard.schemas import (
    CountryRankOut,
    DeveloperRankOut,
    ProjectRankOut,
)
from app.modules.projects.models import Project, ProjectFeedback, ProjectLike
from app.modules.reputation.models import ReputationTransaction
from app.modules.users.models import User


def _period_start(period: str) -> datetime | None:
    now = datetime.now(UTC)
    if period == "week":
        return now - timedelta(days=7)
    if period == "month":
        return now - timedelta(days=30)
    return None


async def developer_leaderboard(
    db: AsyncSession,
    *,
    period: str,
    country_code: str | None,
    limit: int,
    include_demo: bool,
) -> list[DeveloperRankOut]:
    start = _period_start(period)
    stmt = select(User).where(User.is_active.is_(True))
    if country_code:
        stmt = stmt.join(Country, User.country_id == Country.id).where(
            func.upper(Country.code) == country_code.upper()
        )
    if not include_demo:
        stmt = stmt.where(User.is_demo.is_(False))

    if start is None:
        stmt = stmt.order_by(User.reputation_points.desc(), User.created_at.asc()).limit(limit)
        users = list((await db.execute(stmt)).scalars().unique().all())
        return [
            DeveloperRankOut(
                rank=index + 1,
                user_id=user.id,
                username=user.username,
                full_name=user.full_name,
                avatar_url=user.avatar_url,
                country=CountryOut.model_validate(user.country) if user.country else None,
                level=user.level,
                reputation_points=user.reputation_points,
                period_points=user.reputation_points,
            )
            for index, user in enumerate(users)
        ]

    points_stmt = (
        select(
            ReputationTransaction.user_id,
            func.coalesce(func.sum(ReputationTransaction.points), 0).label("points"),
        )
        .where(
            ReputationTransaction.created_at >= start,
            ReputationTransaction.status == ReputationStatus.APPROVED.value,
        )
        .group_by(ReputationTransaction.user_id)
        .subquery()
    )
    stmt = (
        select(User, points_stmt.c.points)
        .join(points_stmt, points_stmt.c.user_id == User.id)
        .where(User.is_active.is_(True))
        .order_by(points_stmt.c.points.desc())
        .limit(limit)
    )
    if country_code:
        stmt = stmt.join(Country, User.country_id == Country.id).where(
            func.upper(Country.code) == country_code.upper()
        )
    if not include_demo:
        stmt = stmt.where(User.is_demo.is_(False))

    rows = (await db.execute(stmt)).all()
    return [
        DeveloperRankOut(
            rank=index + 1,
            user_id=user.id,
            username=user.username,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
            country=CountryOut.model_validate(user.country) if user.country else None,
            level=user.level,
            reputation_points=user.reputation_points,
            period_points=int(points),
        )
        for index, (user, points) in enumerate(rows)
    ]


async def project_leaderboard(
    db: AsyncSession, *, limit: int, include_demo: bool
) -> list[ProjectRankOut]:
    likes = (
        select(ProjectLike.project_id, func.count().label("likes"))
        .group_by(ProjectLike.project_id)
        .subquery()
    )
    contributors = (
        select(ContributionRequest.project_id, func.count().label("contributors"))
        .where(ContributionRequest.status == "accepted")
        .group_by(ContributionRequest.project_id)
        .subquery()
    )
    feedback = (
        select(ProjectFeedback.project_id, func.count().label("useful"))
        .where(ProjectFeedback.is_useful.is_(True))
        .group_by(ProjectFeedback.project_id)
        .subquery()
    )
    stmt = (
        select(
            Project,
            func.coalesce(likes.c.likes, 0),
            func.coalesce(contributors.c.contributors, 0),
            func.coalesce(feedback.c.useful, 0),
        )
        .outerjoin(likes, likes.c.project_id == Project.id)
        .outerjoin(contributors, contributors.c.project_id == Project.id)
        .outerjoin(feedback, feedback.c.project_id == Project.id)
        .where(Project.is_published.is_(True))
    )
    if not include_demo:
        stmt = stmt.where(Project.is_demo.is_(False))
    rows = (await db.execute(stmt)).all()

    scored: list[tuple[float, Project, int, int, int]] = []
    for project, like_count, contributor_count, useful_count in rows:
        # Weighted traction: no single metric can dominate, stars are capped.
        score = (
            float(like_count) * 1.0
            + float(contributor_count) * 5.0
            + float(useful_count) * 2.0
            + min(float(project.view_count), 1000.0) * 0.05
            + min(float(project.github_stars), 500) * 0.3
        )
        scored.append((round(score, 2), project, int(like_count), int(contributor_count), int(useful_count)))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        ProjectRankOut(
            rank=index + 1,
            project_id=project.id,
            name=project.name,
            slug=project.slug,
            creator_username=project.creator.username if project.creator else "unknown",
            country=CountryOut.model_validate(project.country) if project.country else None,
            likes=like_count,
            accepted_contributors=contributor_count,
            useful_feedback=useful_count,
            visits=project.view_count,
            score=score,
        )
        for index, (score, project, like_count, contributor_count, useful_count) in enumerate(
            scored[:limit]
        )
    ]


async def country_leaderboard(db: AsyncSession, *, limit: int, include_demo: bool) -> list[CountryRankOut]:
    stmt = (
        select(
            Country,
            func.count(User.id),
            func.coalesce(func.sum(User.reputation_points), 0),
        )
        .join(User, User.country_id == Country.id)
        .where(User.is_active.is_(True), User.reputation_points > 0)
        .group_by(Country.id)
    )
    if not include_demo:
        stmt = stmt.where(User.is_demo.is_(False))
    rows = (await db.execute(stmt)).all()
    ranked = []
    for country, developers, total_points in rows:
        average = round(float(total_points) / developers, 2) if developers else 0.0
        ranked.append((average, country, int(developers), int(total_points)))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [
        CountryRankOut(
            rank=index + 1,
            country=CountryOut.model_validate(country),
            active_developers=developers,
            total_points=total_points,
            average_points=average,
        )
        for index, (average, country, developers, total_points) in enumerate(ranked[:limit])
    ]


def demo_default() -> bool:
    return settings.demo_mode
