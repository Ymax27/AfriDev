"""Notification creation and listing."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.notifications.models import Notification


async def notify(
    db: AsyncSession,
    *,
    user_id: UUID,
    type: str,
    title: str,
    body: str | None = None,
    link: str | None = None,
) -> Notification:
    notification = Notification(user_id=user_id, type=type, title=title, body=body, link=link)
    db.add(notification)
    await db.flush()
    return notification


async def list_for_user(
    db: AsyncSession, user_id: UUID, *, unread_only: bool, page: int, page_size: int
) -> tuple[list[Notification], int]:
    stmt = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        stmt = stmt.where(Notification.is_read.is_(False))
    stmt = stmt.order_by(Notification.created_at.desc())
    total = int((await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one())
    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().all()), total


async def mark_read(db: AsyncSession, notification_id: UUID, user_id: UUID) -> Notification:
    notification = await db.get(Notification, notification_id)
    if not notification:
        raise NotFoundError("Notification not found")
    if notification.user_id != user_id:
        raise ForbiddenError("This notification belongs to another user")
    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return notification
