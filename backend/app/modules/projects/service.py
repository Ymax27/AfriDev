"""Project publication, discovery and interaction services."""

import secrets
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import String, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ReputationAction, VerificationStatus
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.core.utils import unique_slug
from app.modules.contributions.models import ContributionRequest
from app.modules.countries.models import Country
from app.modules.projects.models import (
    OwnershipVerification,
    Project,
    ProjectFeedback,
    ProjectLike,
    ProjectPass,
)
from app.modules.projects.schemas import ProjectCreate, ProjectOut, ProjectUpdate
from app.modules.reputation import service as reputation_service
from app.modules.users.models import User


async def get_project(db: AsyncSession, project_id: UUID) -> Project:
    project = await db.get(Project, project_id)
    if not project:
        raise NotFoundError("Project not found")
    return project


async def _counts(db: AsyncSession, project_ids: list[UUID]) -> dict[UUID, dict[str, int]]:
    if not project_ids:
        return {}
    likes = dict(
        (
            await db.execute(
                select(ProjectLike.project_id, func.count())
                .where(ProjectLike.project_id.in_(project_ids))
                .group_by(ProjectLike.project_id)
            )
        ).all()
    )
    feedback = dict(
        (
            await db.execute(
                select(ProjectFeedback.project_id, func.count())
                .where(ProjectFeedback.project_id.in_(project_ids))
                .group_by(ProjectFeedback.project_id)
            )
        ).all()
    )
    contributions = dict(
        (
            await db.execute(
                select(ContributionRequest.project_id, func.count())
                .where(
                    ContributionRequest.project_id.in_(project_ids),
                    ContributionRequest.status == "accepted",
                )
                .group_by(ContributionRequest.project_id)
            )
        ).all()
    )
    return {
        project_id: {
            "likes": int(likes.get(project_id, 0)),
            "feedback": int(feedback.get(project_id, 0)),
            "contributions": int(contributions.get(project_id, 0)),
        }
        for project_id in project_ids
    }


async def serialise_projects(
    db: AsyncSession, projects: list[Project], viewer: User | None
) -> list[ProjectOut]:
    ids = [project.id for project in projects]
    counts = await _counts(db, ids)
    liked: set[UUID] = set()
    passed: set[UUID] = set()
    if viewer and ids:
        liked = set(
            (
                await db.execute(
                    select(ProjectLike.project_id).where(
                        ProjectLike.user_id == viewer.id, ProjectLike.project_id.in_(ids)
                    )
                )
            ).scalars().all()
        )
        passed = set(
            (
                await db.execute(
                    select(ProjectPass.project_id).where(
                        ProjectPass.user_id == viewer.id, ProjectPass.project_id.in_(ids)
                    )
                )
            ).scalars().all()
        )
    output = []
    for project in projects:
        data = ProjectOut.model_validate(project)
        stats = counts.get(project.id, {})
        output.append(
            data.model_copy(
                update={
                    "likes_count": stats.get("likes", 0),
                    "feedback_count": stats.get("feedback", 0),
                    "contributions_count": stats.get("contributions", 0),
                    "liked_by_me": project.id in liked,
                    "passed_by_me": project.id in passed,
                }
            )
        )
    return output


async def resolve_country(db: AsyncSession, code: str | None) -> UUID | None:
    if not code:
        return None
    country = (
        await db.execute(select(Country).where(func.upper(Country.code) == code.upper()))
    ).scalar_one_or_none()
    if not country:
        raise ValidationError("Unknown country code")
    return country.id


async def create_project(db: AsyncSession, creator: User, payload: ProjectCreate) -> Project:
    country_id = await resolve_country(db, payload.country_code)
    project = Project(
        creator_id=creator.id,
        country_id=country_id or creator.country_id,
        name=payload.name,
        slug=await unique_slug(db, Project, f"{payload.name}-{creator.username}"),
        description=payload.description,
        repository_url=payload.repository_url,
        demo_url=payload.demo_url,
        cover_image_url=payload.cover_image_url,
        technologies=payload.technologies,
        tags=payload.tags,
        category=payload.category,
        collaboration_mode=payload.collaboration_mode.value,
        is_published=True,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def update_project(
    db: AsyncSession, project: Project, user: User, payload: ProjectUpdate
) -> Project:
    if project.creator_id != user.id and not user.is_admin:
        raise ForbiddenError("Only the project owner can update this project")
    data = payload.model_dump(exclude_unset=True)
    country_code = data.pop("country_code", None)
    if country_code:
        project.country_id = await resolve_country(db, country_code)
    if "collaboration_mode" in data and data["collaboration_mode"] is not None:
        data["collaboration_mode"] = data["collaboration_mode"].value
    for field, value in data.items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    return project


async def list_projects(
    db: AsyncSession,
    *,
    viewer: User | None,
    q: str | None,
    country_code: str | None,
    technology: str | None,
    mode: str | None,
    category: str | None,
    creator_username: str | None,
    sort: str,
    page: int,
    page_size: int,
    exclude_interacted: bool = False,
) -> tuple[list[Project], int]:
    stmt = select(Project).where(Project.is_published.is_(True))
    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(
            func.lower(Project.name).like(pattern) | func.lower(Project.description).like(pattern)
        )
    if country_code:
        stmt = stmt.join(Country, Project.country_id == Country.id).where(
            func.upper(Country.code) == country_code.upper()
        )
    if technology:
        stmt = stmt.where(func.lower(cast(Project.technologies, String)).contains(technology.lower()))
    if mode:
        stmt = stmt.where(Project.collaboration_mode == mode)
    if category:
        stmt = stmt.where(Project.category == category)
    if creator_username:
        stmt = stmt.join(User, Project.creator_id == User.id).where(
            func.lower(User.username) == creator_username.lower()
        )
    if exclude_interacted and viewer:
        liked = select(ProjectLike.project_id).where(ProjectLike.user_id == viewer.id)
        passed = select(ProjectPass.project_id).where(ProjectPass.user_id == viewer.id)
        stmt = stmt.where(Project.id.not_in(liked), Project.id.not_in(passed))

    if sort == "popular":
        likes = (
            select(func.count(ProjectLike.id))
            .where(ProjectLike.project_id == Project.id)
            .scalar_subquery()
        )
        stmt = stmt.order_by(likes.desc(), Project.created_at.desc())
    elif sort == "oldest":
        stmt = stmt.order_by(Project.created_at.asc())
    else:
        stmt = stmt.order_by(Project.created_at.desc())

    total = int((await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one())
    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().unique().all()), total


async def like_project(db: AsyncSession, project: Project, user: User) -> None:
    if project.creator_id == user.id:
        raise ForbiddenError("You cannot like your own project")
    existing = (
        await db.execute(
            select(ProjectLike).where(ProjectLike.project_id == project.id, ProjectLike.user_id == user.id)
        )
    ).scalar_one_or_none()
    if existing:
        return
    db.add(ProjectLike(project_id=project.id, user_id=user.id))
    await db.commit()


async def pass_project(db: AsyncSession, project: Project, user: User) -> None:
    existing = (
        await db.execute(
            select(ProjectPass).where(ProjectPass.project_id == project.id, ProjectPass.user_id == user.id)
        )
    ).scalar_one_or_none()
    if existing:
        return
    db.add(ProjectPass(project_id=project.id, user_id=user.id))
    await db.commit()


async def add_feedback(
    db: AsyncSession, project: Project, author: User, concept: str, improvement: str, feature: str
) -> ProjectFeedback:
    if project.collaboration_mode != "feedback":
        raise ForbiddenError("This project does not accept structured feedback")
    existing = (
        await db.execute(
            select(ProjectFeedback).where(
                ProjectFeedback.project_id == project.id, ProjectFeedback.author_id == author.id
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise ConflictError("You already submitted feedback for this project")
    feedback = ProjectFeedback(
        project_id=project.id,
        author_id=author.id,
        concept_answer=concept,
        improvement_answer=improvement,
        feature_answer=feature,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return feedback


async def mark_feedback_useful(
    db: AsyncSession, feedback: ProjectFeedback, user: User
) -> ProjectFeedback:
    project = await get_project(db, feedback.project_id)
    if project.creator_id != user.id and not user.is_admin:
        raise ForbiddenError("Only the project owner can mark feedback as useful")
    if feedback.is_useful:
        return feedback
    feedback.is_useful = True
    await reputation_service.award(
        db,
        user_id=feedback.author_id,
        actor_id=user.id,
        action_type=ReputationAction.USEFUL_FEEDBACK.value,
        reference_type="project_feedback",
        reference_id=str(feedback.id),
        is_demo=feedback.is_demo,
    )
    await db.commit()
    await db.refresh(feedback)
    return feedback


async def list_feedback(db: AsyncSession, project: Project) -> list[ProjectFeedback]:
    result = await db.execute(
        select(ProjectFeedback)
        .where(ProjectFeedback.project_id == project.id)
        .order_by(ProjectFeedback.created_at.desc())
    )
    return list(result.scalars().all())


async def start_ownership_verification(
    db: AsyncSession, project: Project, user: User, method: str
) -> OwnershipVerification:
    if project.creator_id != user.id:
        raise ForbiddenError("Only the project owner can request verification")
    if project.ownership_status == VerificationStatus.VERIFIED.value:
        raise ConflictError("Project is already verified")
    record = OwnershipVerification(
        project_id=project.id,
        user_id=user.id,
        method=method,
        challenge_token=f"afridev-verify-{secrets.token_hex(8)}",
        status=VerificationStatus.PENDING.value,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def confirm_ownership_verification(
    db: AsyncSession, verification: OwnershipVerification, user: User, token: str
) -> OwnershipVerification:
    project = await get_project(db, verification.project_id)
    if project.creator_id != user.id and not user.is_admin:
        raise ForbiddenError("Only the project owner can confirm verification")
    if verification.status != VerificationStatus.PENDING.value:
        raise ConflictError("Verification already resolved")
    if token.strip() != verification.challenge_token:
        verification.status = VerificationStatus.REJECTED.value
        await db.commit()
        raise ValidationError("Verification token does not match the challenge")
    verification.status = VerificationStatus.VERIFIED.value
    verification.verified_at = datetime.now(UTC)
    project.ownership_status = VerificationStatus.VERIFIED.value
    await reputation_service.award(
        db,
        user_id=project.creator_id,
        actor_id=user.id,
        action_type=ReputationAction.VERIFIED_PROJECT_PUBLICATION.value,
        reference_type="project",
        reference_id=str(project.id),
        is_demo=project.is_demo,
    )
    await db.commit()
    await db.refresh(verification)
    return verification
