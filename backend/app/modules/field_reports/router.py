"""Field report endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import CurrentUser, DbSession, Pagination
from app.core.rate_limit import rate_limit
from app.modules.field_reports import service
from app.modules.field_reports.schemas import (
    ConfirmationCreate,
    ConfirmationOut,
    FieldReportListOut,
    FieldReportOut,
    FieldReportUpdate,
)

router = APIRouter(prefix="/field-reports", tags=["field-reports"])


@router.get("", response_model=FieldReportListOut)
async def list_field_reports(
    db: DbSession,
    paging: Annotated[Pagination, Depends()],
    q: str | None = Query(default=None, max_length=100),
    country: str | None = Query(default=None, min_length=2, max_length=2),
    api_entry_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
) -> FieldReportListOut:
    reports, total = await service.list_reports(
        db,
        q=q,
        country_code=country,
        api_entry_id=api_entry_id,
        status=status,
        page=paging.page,
        page_size=paging.page_size,
    )
    items = []
    for report in reports:
        item = FieldReportOut.model_validate(report)
        items.append(item.model_copy(update={"status": service.effective_status(report)}))
    return FieldReportListOut(items=items, total=total, page=paging.page, page_size=paging.page_size)


@router.get("/{report_id}", response_model=FieldReportOut)
async def read_field_report(report_id: UUID, db: DbSession) -> FieldReportOut:
    report = await service.get_report(db, report_id)
    item = FieldReportOut.model_validate(report)
    return item.model_copy(update={"status": service.effective_status(report)})


@router.patch("/{report_id}", response_model=FieldReportOut)
async def update_field_report(
    report_id: UUID, payload: FieldReportUpdate, user: CurrentUser, db: DbSession
) -> FieldReportOut:
    report = await service.get_report(db, report_id)
    updated = await service.update_report(db, report, user, payload)
    return FieldReportOut.model_validate(updated)


@router.get("/{report_id}/confirmations", response_model=list[ConfirmationOut])
async def list_confirmations(report_id: UUID, db: DbSession) -> list[ConfirmationOut]:
    await service.get_report(db, report_id)
    return [
        ConfirmationOut.model_validate(item)
        for item in await service.list_confirmations(db, report_id)
    ]


@router.post(
    "/{report_id}/confirm",
    response_model=FieldReportOut,
    status_code=201,
    dependencies=[Depends(rate_limit(20, 3600, scope="report-confirm"))],
)
async def confirm_field_report(
    report_id: UUID, payload: ConfirmationCreate, user: CurrentUser, db: DbSession
) -> FieldReportOut:
    report = await service.get_report(db, report_id)
    updated = await service.confirm_report(db, report, user, payload.comment)
    item = FieldReportOut.model_validate(updated)
    return item.model_copy(update={"status": service.effective_status(updated)})
