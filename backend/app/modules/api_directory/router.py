"""API directory endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import CurrentUser, DbSession, Pagination
from app.modules.api_directory import service
from app.modules.api_directory.schemas import (
    APICategoryOut,
    APIEntryListOut,
    APIEntryOut,
    APIEntryUpdate,
)

router = APIRouter(prefix="/apis", tags=["api-directory"])


@router.get("", response_model=APIEntryListOut)
async def list_apis(
    db: DbSession,
    paging: Annotated[Pagination, Depends()],
    q: str | None = Query(default=None, max_length=100),
    category: str | None = Query(default=None, max_length=60),
    country: str | None = Query(default=None, min_length=2, max_length=2),
) -> APIEntryListOut:
    entries, total = await service.list_entries(
        db, q=q, category=category, country_code=country, page=paging.page, page_size=paging.page_size
    )
    counts = await service.related_report_counts(db, [entry.id for entry in entries])
    items = [
        APIEntryOut.model_validate(entry).model_copy(
            update={"related_field_reports": counts.get(entry.id, 0)}
        )
        for entry in entries
    ]
    return APIEntryListOut(items=items, total=total, page=paging.page, page_size=paging.page_size)


@router.get("/categories", response_model=list[APICategoryOut])
async def list_categories(db: DbSession) -> list[APICategoryOut]:
    return [APICategoryOut(category=name, count=count) for name, count in await service.categories(db)]


@router.patch("/{entry_id}", response_model=APIEntryOut)
async def update_api(
    entry_id: UUID, payload: APIEntryUpdate, user: CurrentUser, db: DbSession
) -> APIEntryOut:
    entry = await service.get_entry(db, entry_id)
    updated = await service.update_entry(db, entry, user, payload)
    counts = await service.related_report_counts(db, [updated.id])
    return APIEntryOut.model_validate(updated).model_copy(
        update={"related_field_reports": counts.get(updated.id, 0)}
    )


@router.get("/{entry_id}", response_model=APIEntryOut)
async def read_api(entry_id: UUID, db: DbSession) -> APIEntryOut:
    entry = await service.get_entry(db, entry_id)
    counts = await service.related_report_counts(db, [entry.id])
    return APIEntryOut.model_validate(entry).model_copy(
        update={"related_field_reports": counts.get(entry.id, 0)}
    )
