"""Read-only MCP tool: search publicly valid field reports."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.countries.models import Country
from app.modules.field_reports.models import FieldReport


async def search_field_reports(
    db: AsyncSession, query: str = "", country: str | None = None, limit: int = 10
) -> dict[str, Any]:
    limit = max(1, min(limit, 25))
    stmt = (
        select(FieldReport)
        .where(FieldReport.status != "archived")
        .order_by(FieldReport.last_validated_at.desc().nulls_last(), FieldReport.created_at.desc())
        .limit(limit)
    )
    if query:
        pattern = f"%{query.lower()}%"
        stmt = stmt.where(
            func.lower(FieldReport.title).like(pattern)
            | func.lower(FieldReport.solution_summary).like(pattern)
        )
    if country:
        stmt = stmt.join(Country, FieldReport.country_id == Country.id).where(
            func.upper(Country.code) == country.upper()
        )
    reports = (await db.execute(stmt)).scalars().unique().all()
    return {
        "tool": "search_field_reports",
        "source": "afridev-hub://field-reports",
        "count": len(reports),
        "results": [
            {
                "id": str(report.id),
                "title": report.title,
                "country": report.country.code if report.country else None,
                "status": report.status,
                "confirmation_count": report.confirmation_count,
                "solution_summary": report.solution_summary[:600],
                "last_validated_at": report.last_validated_at.isoformat()
                if report.last_validated_at
                else None,
            }
            for report in reports
        ],
    }
