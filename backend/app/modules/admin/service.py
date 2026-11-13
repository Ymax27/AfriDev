"""Administrative operations with audit logging."""

import logging
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ReputationStatus
from app.core.exceptions import ConflictError, NotFoundError
from app.modules.admin.schemas import AdminOverview, AdminUserOut
from app.modules.api_directory.models import APIEntry
from app.modules.field_reports.models import FieldReport
from app.modules.knowledge.models import KnowledgeProblem
from app.modules.messaging.models import Conversation, ConversationMember
from app.modules.missions.models import Mission
from app.modules.moderation.models import ContentReport
from app.modules.projects.models import Project
from app.modules.reputation import service as reputation_service
from app.modules.reputation.models import ReputationTransaction
from app.modules.users.models import User

logger = logging.getLogger("afridev.audit")


async def overview(db: AsyncSession) -> AdminOverview:
    async def count(model, *conditions) -> int:
        stmt = select(func.count()).select_from(model)
        if conditions:
            stmt = stmt.where(*conditions)
        return int((await db.execute(stmt)).scalar_one())

    points = await db.execute(
        select(func.coalesce(func.sum(ReputationTransaction.points), 0)).where(
            ReputationTransaction.status == ReputationStatus.APPROVED.value
        )
    )
    return AdminOverview(
        users=await count(User),
        active_users=await count(User, User.is_active.is_(True)),
        demo_users=await count(User, User.is_demo.is_(True)),
        projects=await count(Project),
        problems=await count(KnowledgeProblem),
        field_reports=await count(FieldReport),
        missions=await count(Mission),
        api_entries=await count(APIEntry),
        open_reports=await count(ContentReport, ContentReport.status == "open"),
        reputation_transactions=await count(ReputationTransaction),
        points_awarded=int(points.scalar_one()),
    )


async def list_users(
    db: AsyncSession, *, query: str | None, page: int, page_size: int
) -> tuple[list[AdminUserOut], int]:
    stmt = select(User).order_by(User.created_at.desc())
    if query:
        stmt = stmt.where(func.lower(User.username).contains(query.lower()))
    total = int((await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one())
    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    users = list(result.scalars().unique().all())
    return [
        AdminUserOut(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_admin=user.is_admin,
            is_demo=user.is_demo,
            reputation_points=user.reputation_points,
            level=user.level,
            reputation_frozen=user.reputation_frozen,
            country_code=user.country.code if user.country else None,
        )
        for user in users
    ], total


async def set_active(db: AsyncSession, user_id: UUID, admin: User, active: bool) -> User:
    target = await db.get(User, user_id)
    if not target:
        raise NotFoundError("User not found")
    if target.id == admin.id and not active:
        raise ConflictError("You cannot suspend your own account")
    target.is_active = active
    logger.info(
        "admin account status changed",
        extra={"user_id": str(admin.id), "path": f"/admin/users/{user_id}", "status_code": 200},
    )
    await db.commit()
    await db.refresh(target)
    return target


async def set_reputation_frozen(db: AsyncSession, user_id: UUID, admin: User, frozen: bool) -> User:
    target = await db.get(User, user_id)
    if not target:
        raise NotFoundError("User not found")
    target.reputation_frozen = frozen
    logger.info(
        "admin reputation freeze changed",
        extra={"user_id": str(admin.id), "path": f"/admin/users/{user_id}", "status_code": 200},
    )
    await db.commit()
    await db.refresh(target)
    return target


async def purge_demo_content(db: AsyncSession, admin: User) -> dict[str, int]:
    """Delete demo records only. Real user data is never touched."""
    demo_users = (
        await db.execute(select(User.id).where(User.is_demo.is_(True)))
    ).scalars().all()
    removed_users = len(demo_users)
    await db.execute(delete(ReputationTransaction).where(ReputationTransaction.is_demo.is_(True)))
    await db.execute(delete(APIEntry).where(APIEntry.is_demo.is_(True)))
    if demo_users:
        await db.execute(delete(User).where(User.id.in_(demo_users)))
    orphan_members = ~select(ConversationMember.conversation_id)
    removed_conversations = 0
    for conversation in (
        await db.execute(select(Conversation).where(Conversation.id.not_in(orphan_members)))
    ).scalars().all():
        if conversation.type == "contribution":
            await db.delete(conversation)
            removed_conversations += 1
    logger.info(
        "admin purged demo content",
        extra={"user_id": str(admin.id), "path": "/admin/demo/purge", "status_code": 200},
    )
    await db.commit()
    return {"users": removed_users, "conversations": removed_conversations}


async def recalculate_reputation(db: AsyncSession, admin: User) -> int:
    count = await reputation_service.recalculate_all(db)
    logger.info(
        "admin recalculated reputation",
        extra={"user_id": str(admin.id), "path": "/admin/reputation/recalculate", "status_code": 200},
    )
    return count
