"""Small shared helpers."""

import re
import unicodedata
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


def slugify(value: str, max_length: int = 160) -> str:
    normalised = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalised).strip("-").lower()
    return (slug or "item")[:max_length]


async def unique_slug(session: AsyncSession, model: type, base_value: str) -> str:
    base = slugify(base_value)
    candidate = base
    suffix = 2
    while True:
        existing = await session.execute(select(model.id).where(model.slug == candidate).limit(1))
        if existing.scalar_one_or_none() is None:
            return candidate
        candidate = f"{base}-{suffix}"
        suffix += 1


def as_uuid(value: str | UUID) -> UUID:
    return value if isinstance(value, UUID) else UUID(value)


def level_for_points(points: int) -> str:
    if points >= 500:
        return "expert"
    if points >= 200:
        return "confirmed"
    if points >= 50:
        return "contributor"
    return "newcomer"


async def count_of(session: AsyncSession, stmt) -> int:
    return int((await session.execute(stmt)).scalar_one())


def scalar_count(stmt):
    return select(func.count()).select_from(stmt.subquery())
