"""Sponsored missions and submission review."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import MissionStatus, ReputationAction
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.utils import unique_slug
from app.modules.missions.models import Mission, MissionSubmission
from app.modules.missions.schemas import MissionCreate
from app.modules.notifications import service as notification_service
from app.modules.projects.service import resolve_country
from app.modules.reputation import service as reputation_service
from app.modules.users.models import User


async def create_mission(db: AsyncSession, sponsor: User, payload: MissionCreate) -> Mission:
    mission = Mission(
        sponsor_id=sponsor.id,
        api_entry_id=payload.api_entry_id,
        country_id=await resolve_country(db, payload.country_code),
        title=payload.title,
        slug=await unique_slug(db, Mission, payload.title),
        description=payload.description,
        objectives=payload.objectives,
        required_skills=payload.required_skills,
        reward_points=payload.reward_points,
        reward_description=payload.reward_description,
        deadline=payload.deadline,
        status=payload.status.value,
    )
    db.add(mission)
    await db.commit()
    await db.refresh(mission)
    return mission


async def get_mission(db: AsyncSession, mission_id: UUID) -> Mission:
    mission = await db.get(Mission, mission_id)
    if not mission:
        raise NotFoundError("Mission not found")
    return mission


async def list_missions(
    db: AsyncSession,
    *,
    q: str | None,
    status: str | None,
    country_code: str | None,
    skill: str | None,
    page: int,
    page_size: int,
) -> tuple[list[Mission], int]:
    from app.modules.countries.models import Country

    stmt = select(Mission).order_by(Mission.created_at.desc())
    if q:
        stmt = stmt.where(func.lower(Mission.title).like(f"%{q.lower()}%"))
    if status:
        stmt = stmt.where(Mission.status == status)
    else:
        stmt = stmt.where(Mission.status != MissionStatus.DRAFT.value)
    if country_code:
        stmt = stmt.join(Country, Mission.country_id == Country.id).where(
            func.upper(Country.code) == country_code.upper()
        )
    if skill:
        from sqlalchemy import String, cast

        stmt = stmt.where(func.lower(cast(Mission.required_skills, String)).contains(skill.lower()))
    total = int((await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one())
    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().unique().all()), total


async def submissions_count(db: AsyncSession, mission_ids: list[UUID]) -> dict[UUID, int]:
    if not mission_ids:
        return {}
    rows = (
        await db.execute(
            select(MissionSubmission.mission_id, func.count())
            .where(MissionSubmission.mission_id.in_(mission_ids))
            .group_by(MissionSubmission.mission_id)
        )
    ).all()
    return {mission_id: int(count) for mission_id, count in rows}


async def create_submission(
    db: AsyncSession, mission: Mission, developer: User, summary: str, solution_url: str | None
) -> MissionSubmission:
    if mission.sponsor_id == developer.id:
        raise ForbiddenError("You cannot submit to your own mission")
    if mission.status not in {MissionStatus.PUBLISHED.value, MissionStatus.IN_PROGRESS.value}:
        raise ConflictError("This mission is not accepting submissions")
    existing = (
        await db.execute(
            select(MissionSubmission).where(
                MissionSubmission.mission_id == mission.id,
                MissionSubmission.developer_id == developer.id,
                MissionSubmission.status.in_(["submitted", "under_review", "approved"]),
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise ConflictError("You already submitted a solution for this mission")
    submission = MissionSubmission(
        mission_id=mission.id,
        developer_id=developer.id,
        summary=summary,
        solution_url=solution_url,
        status="submitted",
    )
    db.add(submission)
    mission.status = MissionStatus.SUBMITTED.value
    await notification_service.notify(
        db,
        user_id=mission.sponsor_id,
        type="mission_submission",
        title=f"New submission for {mission.title}",
        body=summary[:180],
        link=f"/missions/{mission.id}",
    )
    await db.commit()
    await db.refresh(submission)
    return submission


async def get_submission(db: AsyncSession, submission_id: UUID) -> MissionSubmission:
    submission = await db.get(MissionSubmission, submission_id)
    if not submission:
        raise NotFoundError("Mission submission not found")
    return submission


async def review_submission(
    db: AsyncSession, submission: MissionSubmission, reviewer: User, approve: bool, note: str | None
) -> MissionSubmission:
    mission = await get_mission(db, submission.mission_id)
    if mission.sponsor_id != reviewer.id and not reviewer.is_admin:
        raise ForbiddenError("Only the mission sponsor can review submissions")
    if submission.status in {"approved", "rejected"}:
        raise ConflictError("This submission has already been reviewed")

    submission.status = "approved" if approve else "rejected"
    submission.review_note = note
    submission.reviewed_at = datetime.now(UTC)
    if approve:
        submission.points_awarded = mission.reward_points
        mission.status = MissionStatus.COMPLETED.value
        await reputation_service.award(
            db,
            user_id=submission.developer_id,
            actor_id=reviewer.id,
            action_type=ReputationAction.APPROVED_MISSION.value,
            reference_type="mission_submission",
            reference_id=str(submission.id),
            points=mission.reward_points,
            is_demo=mission.is_demo,
        )
    await notification_service.notify(
        db,
        user_id=submission.developer_id,
        type="mission_reviewed",
        title=f"Mission submission {'approved' if approve else 'rejected'}",
        body=note or mission.title,
        link=f"/missions/{mission.id}",
    )
    await db.commit()
    await db.refresh(submission)
    return submission


async def list_submissions(db: AsyncSession, mission_id: UUID) -> list[MissionSubmission]:
    result = await db.execute(
        select(MissionSubmission)
        .where(MissionSubmission.mission_id == mission_id)
        .order_by(MissionSubmission.created_at.desc())
    )
    return list(result.scalars().all())
