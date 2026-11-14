"""Content reporting and user blocking."""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.modules.moderation.models import ContentReport
from app.modules.users.models import User, UserBlock

logger = logging.getLogger("afridev.audit")


def _is_uuid(value: str) -> bool:
    try:
        UUID(value)
    except ValueError:
        return False
    return True


async def blocked_between(db: AsyncSession, first_id: UUID, second_id: UUID) -> bool:
    """True when either side blocked the other; used to gate chat and requests."""
    result = await db.execute(
        select(UserBlock.id).where(
            or_(
                (UserBlock.blocker_id == first_id) & (UserBlock.blocked_id == second_id),
                (UserBlock.blocker_id == second_id) & (UserBlock.blocked_id == first_id),
            )
        )
    )
    return result.first() is not None


async def create_report(
    db: AsyncSession, reporter: User, target_type: str, target_id: str, reason: str, details: str | None
) -> ContentReport:
    report = ContentReport(
        reporter_id=reporter.id, target_type=target_type, target_id=target_id, reason=reason, details=details
    )
    db.add(report)

    if target_type == "user":
        # Reported accounts have their points frozen for a few days while moderation runs.
        target = await db.get(User, UUID(target_id)) if _is_uuid(target_id) else None
        if target is not None and target.id != reporter.id:
            target.reputation_frozen_until = datetime.now(UTC) + timedelta(days=3)
            logger.info(
                "reported account reputation frozen",
                extra={"user_id": str(target.id), "path": "/reports", "status_code": 201},
            )

    await db.commit()
    await db.refresh(report)
    return report


async def list_reports(
    db: AsyncSession, *, status: str | None, page: int, page_size: int
) -> tuple[list[ContentReport], int]:
    stmt = select(ContentReport).order_by(ContentReport.created_at.desc())
    if status:
        stmt = stmt.where(ContentReport.status == status)
    total = int((await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one())
    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().all()), total


async def resolve_report(
    db: AsyncSession, report_id: UUID, admin: User, status: str, note: str | None
) -> ContentReport:
    report = await db.get(ContentReport, report_id)
    if not report:
        raise NotFoundError("Report not found")
    report.status = status
    report.resolution_note = note
    report.reviewed_by = admin.id
    from datetime import datetime

    report.reviewed_at = datetime.now(UTC)
    logger.info(
        "moderation report resolved",
        extra={"user_id": str(admin.id), "path": f"/reports/{report_id}", "status_code": 200},
    )
    await db.commit()
    await db.refresh(report)
    return report


async def block_user(db: AsyncSession, blocker: User, username: str, reason: str | None) -> UserBlock:
    target = (
        await db.execute(select(User).where(func.lower(User.username) == username.lower()))
    ).scalar_one_or_none()
    if not target:
        raise NotFoundError("User not found")
    if target.id == blocker.id:
        raise ConflictError("You cannot block yourself")
    existing = (
        await db.execute(
            select(UserBlock).where(UserBlock.blocker_id == blocker.id, UserBlock.blocked_id == target.id)
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    block = UserBlock(blocker_id=blocker.id, blocked_id=target.id, reason=reason)
    db.add(block)
    await db.commit()
    await db.refresh(block)
    return block


async def unblock_user(db: AsyncSession, blocker: User, block_id: UUID) -> None:
    block = await db.get(UserBlock, block_id)
    if not block or block.blocker_id != blocker.id:
        raise NotFoundError("Block not found")
    await db.delete(block)
    await db.commit()


async def list_blocks(db: AsyncSession, blocker: User) -> list[tuple[UserBlock, User]]:
    rows = (
        await db.execute(
            select(UserBlock, User)
            .join(User, User.id == UserBlock.blocked_id)
            .where(UserBlock.blocker_id == blocker.id)
            .order_by(UserBlock.created_at.desc())
        )
    ).all()
    return [(block, user) for block, user in rows]
