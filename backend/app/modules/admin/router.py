"""Admin dashboard endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import AdminUser, DbSession, Pagination
from app.modules.admin import service
from app.modules.admin.schemas import AdminOverview, AdminUserListOut
from app.modules.field_reports import service as field_report_service
from app.modules.moderation import service as moderation_service
from app.modules.moderation.schemas import ReportOut, ReportResolve
from app.modules.users.schemas import UserOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview", response_model=AdminOverview)
async def admin_overview(_: AdminUser, db: DbSession) -> AdminOverview:
    return await service.overview(db)


@router.get("/users", response_model=AdminUserListOut)
async def admin_users(
    _: AdminUser,
    db: DbSession,
    paging: Annotated[Pagination, Depends()],
    q: str | None = Query(default=None, max_length=80),
) -> AdminUserListOut:
    items, total = await service.list_users(
        db, query=q, page=paging.page, page_size=paging.page_size
    )
    return AdminUserListOut(items=items, total=total, page=paging.page, page_size=paging.page_size)


@router.post("/users/{user_id}/suspend", response_model=UserOut)
async def suspend_user(user_id: UUID, admin: AdminUser, db: DbSession) -> UserOut:
    return UserOut.model_validate(await service.set_active(db, user_id, admin, False))


@router.post("/users/{user_id}/reactivate", response_model=UserOut)
async def reactivate_user(user_id: UUID, admin: AdminUser, db: DbSession) -> UserOut:
    return UserOut.model_validate(await service.set_active(db, user_id, admin, True))


@router.post("/users/{user_id}/freeze-reputation", response_model=UserOut)
async def freeze_reputation(user_id: UUID, admin: AdminUser, db: DbSession) -> UserOut:
    return UserOut.model_validate(await service.set_reputation_frozen(db, user_id, admin, True))


@router.post("/users/{user_id}/unfreeze-reputation", response_model=UserOut)
async def unfreeze_reputation(user_id: UUID, admin: AdminUser, db: DbSession) -> UserOut:
    return UserOut.model_validate(await service.set_reputation_frozen(db, user_id, admin, False))


@router.get("/reports", response_model=list[ReportOut])
async def admin_reports(
    _: AdminUser,
    db: DbSession,
    paging: Annotated[Pagination, Depends()],
    status: str | None = Query(default=None),
) -> list[ReportOut]:
    items, _total = await moderation_service.list_reports(
        db, status=status, page=paging.page, page_size=paging.page_size
    )
    return [ReportOut.model_validate(item) for item in items]


@router.post("/reports/{report_id}/resolve", response_model=ReportOut)
async def resolve_report(
    report_id: UUID, payload: ReportResolve, admin: AdminUser, db: DbSession
) -> ReportOut:
    return ReportOut.model_validate(
        await moderation_service.resolve_report(
            db, report_id, admin, payload.status, payload.resolution_note
        )
    )


@router.post("/reputation/recalculate")
async def recalculate(admin: AdminUser, db: DbSession) -> dict[str, int]:
    return {"users_recalculated": await service.recalculate_reputation(db, admin)}


@router.post("/field-reports/revalidate")
async def revalidate_field_reports(_: AdminUser, db: DbSession) -> dict[str, int]:
    return {"flagged": await field_report_service.flag_stale_reports(db)}


@router.post("/demo/purge")
async def purge_demo(admin: AdminUser, db: DbSession) -> dict[str, int]:
    return await service.purge_demo_content(db, admin)
