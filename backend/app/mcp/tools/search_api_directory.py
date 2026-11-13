"""Read-only MCP tool: retrieve API directory entries."""

from typing import Any

from sqlalchemy import String, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.api_directory.models import APIEntry


async def search_api_directory(
    db: AsyncSession, query: str = "", category: str | None = None, country: str | None = None, limit: int = 10
) -> dict[str, Any]:
    limit = max(1, min(limit, 25))
    stmt = (
        select(APIEntry)
        .where(APIEntry.is_published.is_(True))
        .order_by(APIEntry.name)
        .limit(limit)
    )
    if query:
        pattern = f"%{query.lower()}%"
        stmt = stmt.where(
            func.lower(APIEntry.name).like(pattern)
            | func.lower(APIEntry.description).like(pattern)
        )
    if category:
        stmt = stmt.where(APIEntry.category == category)
    if country:
        stmt = stmt.where(func.lower(cast(APIEntry.countries, String)).contains(country.lower()))
    entries = (await db.execute(stmt)).scalars().unique().all()
    return {
        "tool": "search_api_directory",
        "source": "afridev-hub://api-directory",
        "count": len(entries),
        "results": [
            {
                "id": str(entry.id),
                "name": entry.name,
                "provider": entry.provider_name,
                "category": entry.category,
                "countries": entry.countries,
                "documentation_url": entry.documentation_url,
                "pricing": entry.pricing,
                "api_status": entry.api_status,
                "integration_notes": (entry.integration_notes or "")[:400],
            }
            for entry in entries
        ],
    }
