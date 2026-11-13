"""Country listing and aggregated country hubs."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.schemas import CountryOut
from app.modules.contributions.models import ContributionRequest
from app.modules.countries.models import Country
from app.modules.countries.schemas import CountryHubOut, CountryStats
from app.modules.field_reports.models import FieldReport
from app.modules.missions.models import Mission
from app.modules.projects.models import Project
from app.modules.users.models import User


async def list_countries(db: AsyncSession) -> list[Country]:
    result = await db.execute(select(Country).where(Country.is_active.is_(True)).order_by(Country.name))
    return list(result.scalars().all())


async def get_country(db: AsyncSession, code: str) -> Country:
    result = await db.execute(select(Country).where(func.upper(Country.code) == code.upper()))
    country = result.scalar_one_or_none()
    if not country:
        raise NotFoundError("Country not found")
    return country


async def build_hub(db: AsyncSession, code: str) -> CountryHubOut:
    country = await get_country(db, code)

    developers = int(
        (
            await db.execute(
                select(func.count(User.id)).where(User.country_id == country.id, User.is_active.is_(True))
            )
        ).scalar_one()
    )
    projects = int(
        (
            await db.execute(
                select(func.count(Project.id)).where(
                    Project.country_id == country.id, Project.is_published.is_(True)
                )
            )
        ).scalar_one()
    )
    reports = int(
        (await db.execute(select(func.count(FieldReport.id)).where(FieldReport.country_id == country.id))).scalar_one()
    )
    contributions = int(
        (
            await db.execute(
                select(func.count(ContributionRequest.id))
                .join(Project, ContributionRequest.project_id == Project.id)
                .where(Project.country_id == country.id, ContributionRequest.status == "accepted")
            )
        ).scalar_one()
    )
    points = int(
        (
            await db.execute(
                select(func.coalesce(func.sum(User.reputation_points), 0)).where(User.country_id == country.id)
            )
        ).scalar_one()
    )

    top_users = (
        await db.execute(
            select(User)
            .where(User.country_id == country.id)
            .order_by(User.reputation_points.desc())
            .limit(5)
        )
    ).scalars().all()
    recent_projects = (
        await db.execute(
            select(Project)
            .where(Project.country_id == country.id, Project.is_published.is_(True))
            .order_by(Project.created_at.desc())
            .limit(4)
        )
    ).scalars().all()
    recent_reports = (
        await db.execute(
            select(FieldReport)
            .where(FieldReport.country_id == country.id)
            .order_by(FieldReport.created_at.desc())
            .limit(4)
        )
    ).scalars().all()
    missions = (
        await db.execute(
            select(Mission)
            .where(Mission.country_id == country.id, Mission.status == "published")
            .order_by(Mission.created_at.desc())
            .limit(4)
        )
    ).scalars().all()

    return CountryHubOut(
        country=CountryOut.model_validate(country),
        stats=CountryStats(
            developers=developers,
            projects=projects,
            field_reports=reports,
            accepted_contributions=contributions,
            reputation_points=points,
            activity_score=country.activity_score,
        ),
        top_developers=[
            {
                "username": user.username,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "level": user.level,
                "reputation_points": user.reputation_points,
            }
            for user in top_users
        ],
        recent_projects=[
            {"id": str(project.id), "name": project.name, "slug": project.slug, "mode": project.collaboration_mode}
            for project in recent_projects
        ],
        recent_field_reports=[
            {"id": str(report.id), "title": report.title, "status": report.status} for report in recent_reports
        ],
        open_missions=[
            {"id": str(mission.id), "title": mission.title, "reward_points": mission.reward_points}
            for mission in missions
        ],
    )
