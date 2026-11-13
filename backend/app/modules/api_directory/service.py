"""Read-mostly African API catalogue."""

from uuid import UUID

from sqlalchemy import String, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.utils import unique_slug
from app.modules.api_directory.models import APIEntry
from app.modules.api_directory.schemas import APIEntryCreate
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


async def create_entry(db: AsyncSession, owner: User, payload: APIEntryCreate) -> APIEntry:
    if not (owner.is_admin or any(role.role in {"api_provider", "sponsor"} for role in owner.roles)):
        raise ForbiddenError("Only API providers or admins can add API entries")
    entry = APIEntry(
        owner_id=owner.id,
        name=payload.name,
        provider_name=payload.provider_name,
        slug=await unique_slug(db, APIEntry, f"{payload.name}-{payload.provider_name}"),
        description=payload.description,
        category=payload.category,
        countries=[code.upper() for code in payload.countries],
        documentation_url=payload.documentation_url,
        pricing=payload.pricing,
        api_status=payload.api_status,
        integration_notes=payload.integration_notes,
    )
    db.add(entry)
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
