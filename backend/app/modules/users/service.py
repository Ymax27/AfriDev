"""User profile services."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.core.utils import level_for_points
from app.modules.contributions.models import ContributionRequest
from app.modules.countries.models import Country
from app.modules.field_reports.models import FieldReport
from app.modules.knowledge.models import Solution
from app.modules.projects.models import Project
from app.modules.users.models import User, UserRole, UserSkill
from app.modules.users.schemas import ProfileUpdate, UserOut, UserProfileOut

ALLOWED_ROLES = {"developer", "project_creator", "api_provider", "company", "admin"}
# Older clients and demo rows used these labels.
ROLE_ALIASES = {"sponsor": "company", "maintainer": "project_creator", "mentor": "developer", "student": "developer"}


async def get_by_username(db: AsyncSession, username: str) -> User:
    result = await db.execute(select(User).where(func.lower(User.username) == username.lower()))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User not found")
    return user


async def get_by_id(db: AsyncSession, user_id: UUID) -> User:
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundError("User not found")
    return user


async def build_profile(db: AsyncSession, user: User) -> UserProfileOut:
    projects = int(
        (await db.execute(select(func.count(Project.id)).where(Project.creator_id == user.id))).scalar_one()
    )
    solutions = int(
        (
            await db.execute(
                select(func.count(Solution.id)).where(Solution.author_id == user.id, Solution.is_accepted.is_(True))
            )
        ).scalar_one()
    )
    reports = int(
        (await db.execute(select(func.count(FieldReport.id)).where(FieldReport.author_id == user.id))).scalar_one()
    )
    verified_projects = int(
        (
            await db.execute(
                select(func.count(Project.id)).where(
                    Project.creator_id == user.id, Project.ownership_status == "verified"
                )
            )
        ).scalar_one()
    )
    merged_contributions = int(
        (
            await db.execute(
                select(func.count(ContributionRequest.id)).where(
                    ContributionRequest.requester_id == user.id,
                    ContributionRequest.merged_at.is_not(None),
                )
            )
        ).scalar_one()
    )
    titles: list[str] = []
    if solutions >= 1:
        titles.append("first_solution")
    if reports >= 3:
        titles.append("field_cartographer")
    if verified_projects >= 3:
        titles.append("verified_builder")
    if merged_contributions >= 1:
        titles.append("team_player")
    if user.reputation_points >= 500:
        titles.append("expert")
    base = UserOut.model_validate(user)
    return UserProfileOut(
        **base.model_dump(),
        projects_count=projects,
        accepted_solutions_count=solutions,
        field_reports_count=reports,
        verified_projects_count=verified_projects,
        merged_contributions_count=merged_contributions,
        titles=titles,
    )


async def update_profile(db: AsyncSession, user: User, payload: ProfileUpdate) -> User:
    data = payload.model_dump(exclude_unset=True)
    country_code = data.pop("country_code", None)
    if country_code:
        country = (
            await db.execute(select(Country).where(func.upper(Country.code) == country_code.upper()))
        ).scalar_one_or_none()
        if not country:
            raise ValidationError("Unknown country code")
        user.country_id = country.id
    roles = data.pop("roles", None)
    skills = data.pop("skills", None)
    if roles is not None or skills is not None:
        # Load collections explicitly; async sessions cannot lazy-load on assignment.
        await db.refresh(user, attribute_names=["roles", "skills"])
    for field, value in data.items():
        setattr(user, field, value)

    if roles is not None:
        cleaned = {ROLE_ALIASES.get(role, role) for role in roles}
        cleaned = {role for role in cleaned if role in ALLOWED_ROLES}
        if user.is_admin:
            cleaned.add("admin")
        else:
            cleaned.discard("admin")
        user.roles.clear()
        await db.flush()
        user.roles.extend(UserRole(role=role) for role in sorted(cleaned))

    if skills is not None:
        user.skills.clear()
        await db.flush()
        user.skills.extend(
            UserSkill(name=name.strip(), level="intermediate") for name in skills if name.strip()
        )

    user.level = level_for_points(user.reputation_points)
    await db.commit()
    await db.refresh(user, attribute_names=["roles", "skills", "country"])
    return user


async def list_users(
    db: AsyncSession, *, query: str | None, country_code: str | None, page: int, page_size: int
) -> tuple[list[User], int]:
    stmt = select(User).where(User.is_active.is_(True)).order_by(User.reputation_points.desc())
    if query:
        stmt = stmt.where(func.lower(User.username).contains(query.lower()))
    if country_code:
        stmt = stmt.join(Country, User.country_id == Country.id).where(func.upper(Country.code) == country_code.upper())
    total = int((await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one())
    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().unique().all()), total


async def attach_user_relations(db: AsyncSession, user: User) -> User:
    await db.refresh(user, attribute_names=["roles", "skills", "country"])
    return user
