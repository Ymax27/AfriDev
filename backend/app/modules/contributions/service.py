"""Contribution request lifecycle."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ContributionStatus, ConversationType, ReputationAction
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.modules.contributions.models import ContributionRequest
from app.modules.contributions.schemas import ContributionCreate
from app.modules.messaging.models import Conversation, ConversationMember, Message
from app.modules.notifications import service as notification_service
from app.modules.projects.models import Project
from app.modules.reputation import service as reputation_service
from app.modules.users.models import User


async def create_request(
    db: AsyncSession, project: Project, requester: User, payload: ContributionCreate
) -> ContributionRequest:
    if project.creator_id == requester.id:
        raise ForbiddenError("You cannot request to contribute to your own project")
    if project.collaboration_mode != "open_to_contributors":
        raise ForbiddenError("This project is not open to contributors")
    existing = (
        await db.execute(
            select(ContributionRequest).where(
                ContributionRequest.project_id == project.id,
                ContributionRequest.requester_id == requester.id,
                ContributionRequest.status.in_(
                    [ContributionStatus.PENDING.value, ContributionStatus.ACCEPTED.value]
                ),
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise ConflictError("You already have an open contribution request for this project")
    request = ContributionRequest(
        project_id=project.id,
        requester_id=requester.id,
        message=payload.message,
        domain=payload.domain.value,
    )
    db.add(request)
    await notification_service.notify(
        db,
        user_id=project.creator_id,
        type="contribution_request",
        title=f"New contribution request for {project.name}",
        body=payload.message[:180],
        link=f"/projects/{project.id}",
    )
    await db.commit()
    await db.refresh(request)
    return request


async def get_request(db: AsyncSession, request_id: UUID) -> ContributionRequest:
    request = await db.get(ContributionRequest, request_id)
    if not request:
        raise NotFoundError("Contribution request not found")
    return request


async def _ensure_maintainer(db: AsyncSession, request: ContributionRequest, user: User) -> Project:
    project = await db.get(Project, request.project_id)
    if project is None:
        raise NotFoundError("Project not found")
    if project.creator_id != user.id and not user.is_admin:
        raise ForbiddenError("Only the project maintainer can review this request")
    return project


async def accept_request(
    db: AsyncSession, request: ContributionRequest, user: User
) -> ContributionRequest:
    project = await _ensure_maintainer(db, request, user)
    if request.status != ContributionStatus.PENDING.value:
        raise ConflictError("This request has already been reviewed")
    request.status = ContributionStatus.ACCEPTED.value
    request.reviewed_at = datetime.now(UTC)
    request.reviewer_id = user.id

    conversation = Conversation(
        type=ConversationType.CONTRIBUTION.value,
        title=f"{project.name} · contribution",
        project_id=project.id,
        contribution_id=request.id,
    )
    db.add(conversation)
    await db.flush()
    db.add_all(
        [
            ConversationMember(conversation_id=conversation.id, user_id=project.creator_id, role="owner"),
            ConversationMember(conversation_id=conversation.id, user_id=request.requester_id, role="member"),
        ]
    )
    first_message = Message(
        conversation_id=conversation.id,
        sender_id=user.id,
        body=f"Your contribution request ({request.domain}) was accepted. Let's collaborate!",
    )
    db.add(first_message)
    conversation.last_message_at = datetime.now(UTC)
    request.conversation_id = conversation.id

    await notification_service.notify(
        db,
        user_id=request.requester_id,
        type="contribution_accepted",
        title=f"Contribution accepted on {project.name}",
        body="A private conversation has been opened with the maintainer.",
        link="/messages",
    )
    await db.commit()
    await db.refresh(request)
    return request


async def reject_request(
    db: AsyncSession, request: ContributionRequest, user: User, reason: str | None = None
) -> ContributionRequest:
    await _ensure_maintainer(db, request, user)
    if request.status != ContributionStatus.PENDING.value:
        raise ConflictError("This request has already been reviewed")
    request.status = ContributionStatus.REJECTED.value
    request.reviewed_at = datetime.now(UTC)
    request.reviewer_id = user.id
    await notification_service.notify(
        db,
        user_id=request.requester_id,
        type="contribution_rejected",
        title="Contribution request declined",
        body=reason or "The maintainer declined this request.",
        link="/discover",
    )
    await db.commit()
    await db.refresh(request)
    return request


async def mark_merged(
    db: AsyncSession, request: ContributionRequest, user: User
) -> ContributionRequest:
    project = await _ensure_maintainer(db, request, user)
    if request.status != ContributionStatus.ACCEPTED.value:
        raise ValidationError("Only accepted contributions can be marked as merged")
    await reputation_service.award(
        db,
        user_id=request.requester_id,
        actor_id=user.id,
        action_type=ReputationAction.MERGED_CONTRIBUTION.value,
        reference_type="contribution_request",
        reference_id=str(request.id),
        is_demo=project.is_demo,
    )
    project.ownership_status = project.ownership_status  # keep value explicit for clarity
    await db.commit()
    await db.refresh(request)
    return request


async def list_for_project(
    db: AsyncSession, project_id: UUID, *, status: str | None, page: int, page_size: int
) -> tuple[list[ContributionRequest], int]:
    stmt = select(ContributionRequest).where(ContributionRequest.project_id == project_id)
    if status:
        stmt = stmt.where(ContributionRequest.status == status)
    stmt = stmt.order_by(ContributionRequest.created_at.desc())
    total = int((await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one())
    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().all()), total


async def list_for_requester(
    db: AsyncSession, user_id: UUID, *, page: int, page_size: int
) -> tuple[list[ContributionRequest], int]:
    stmt = (
        select(ContributionRequest)
        .where(ContributionRequest.requester_id == user_id)
        .order_by(ContributionRequest.created_at.desc())
    )
    total = int((await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one())
    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().all()), total
