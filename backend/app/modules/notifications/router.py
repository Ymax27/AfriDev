"""Notification endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select

from app.api.dependencies import CurrentUser, DbSession, Pagination
from app.modules.notifications import service
from app.modules.notifications.models import Notification
from app.modules.notifications.schemas import NotificationListOut, NotificationOut

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=NotificationListOut)
async def list_notifications(
    user: CurrentUser,
    db: DbSession,
    paging: Annotated[Pagination, Depends()],
    unread_only: bool = Query(default=False),
) -> NotificationListOut:
    items, total = await service.list_for_user(
        db, user.id, unread_only=unread_only, page=paging.page, page_size=paging.page_size
    )
    unread = await db.execute(
        select(func.count(Notification.id)).where(Notification.user_id == user.id, Notification.is_read.is_(False))
    )
    return NotificationListOut(
        items=[NotificationOut.model_validate(item) for item in items],
        total=total,
        page=paging.page,
        page_size=paging.page_size,
        unread_count=int(unread.scalar_one()),
    )


@router.post("/notifications/{notification_id}/read", response_model=NotificationOut)
async def mark_notification_read(notification_id: UUID, user: CurrentUser, db: DbSession) -> NotificationOut:
    return NotificationOut.model_validate(await service.mark_read(db, notification_id, user.id))
