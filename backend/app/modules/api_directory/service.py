"""Read-mostly African API catalogue."""

from uuid import UUID

from sqlalchemy import String, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.api_directory.models import APIEntry
from app.modules.api_directory.schemas import APIEntryUpdate
from app.modules.field_reports.models import FieldReport
from app.modules.users.models import User


async def list_entries(
    db: AsyncSession,
    *,
    q: str | None,
    category: str | None,
    country_code: str | None,
    page: int,
    page_size: int,
) -> tuple[list[APIEntry], int]:
    stmt = select(APIEntry).where(APIEntry.is_published.is_(True)).order_by(APIEntry.name)
    if q:
        pattern = f"%{q.lower()}%"
        stmt = stmt.where(
            func.lower(APIEntry.name).like(pattern)
            | func.lower(APIEntry.provider_name).like(pattern)
            | func.lower(APIEntry.description).like(pattern)
        )
    if category:
        stmt = stmt.where(APIEntry.category == category)
    if country_code:
        stmt = stmt.where(func.lower(cast(APIEntry.countries, String)).contains(country_code.lower()))
    total = int((await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one())
    result = await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))
    return list(result.scalars().unique().all()), total


async def related_report_counts(db: AsyncSession, ids: list[UUID]) -> dict[UUID, int]:
    if not ids:
        return {}
    rows = (
        await db.execute(
            select(FieldReport.api_entry_id, func.count())
            .where(FieldReport.api_entry_id.in_(ids))
            .group_by(FieldReport.api_entry_id)
        )
    ).all()
    return {entry_id: int(count) for entry_id, count in rows if entry_id}


async def get_entry(db: AsyncSession, entry_id: UUID) -> APIEntry:
    entry = await db.get(APIEntry, entry_id)
    if not entry:
        raise NotFoundError("API entry not found")
    return entry


async def get_entry_by_slug(db: AsyncSession, slug: str) -> APIEntry:
    entry = (
        await db.execute(select(APIEntry).where(APIEntry.slug == slug))
    ).scalar_one_or_none()
    if not entry:
        raise NotFoundError("API entry not found")
    return entry


async def update_entry(
    db: AsyncSession, entry: APIEntry, owner: User, payload: APIEntryUpdate
) -> APIEntry:
    """The directory is curated; a provider may only edit the sheet it owns."""
    if not owner.is_admin and entry.owner_id != owner.id:
        raise ForbiddenError("Only the API provider owning this sheet can edit it")
    data = payload.model_dump(exclude_unset=True)
    if "countries" in data and data["countries"] is not None:
        data["countries"] = [code.upper() for code in data["countries"]]
    for field, value in data.items():
        setattr(entry, field, value)
    await db.commit()
    await db.refresh(entry)
    return entry


async def categories(db: AsyncSession) -> list[tuple[str, int]]:
    rows = (
        await db.execute(
            select(APIEntry.category, func.count())
            .where(APIEntry.is_published.is_(True))
            .group_by(APIEntry.category)
            .order_by(func.count().desc())
        )
    ).all()
    return [(str(category), int(count)) for category, count in rows]
