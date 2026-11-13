"""Read-only MCP tool: discover projects accepting contributors."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.countries.models import Country
from app.modules.projects.models import Project


async def search_open_projects(
    db: AsyncSession, query: str = "", country: str | None = None, limit: int = 10
) -> dict[str, Any]:
    limit = max(1, min(limit, 25))
    stmt = (
        select(Project)
        .where(
            Project.is_published.is_(True),
            Project.collaboration_mode == "open_to_contributors",
        )
        .order_by(Project.created_at.desc())
        .limit(limit)
    )
    if query:
        pattern = f"%{query.lower()}%"
        stmt = stmt.where(
            func.lower(Project.name).like(pattern) | func.lower(Project.description).like(pattern)
        )
    if country:
        stmt = stmt.join(Country, Project.country_id == Country.id).where(
            func.upper(Country.code) == country.upper()
        )
    projects = (await db.execute(stmt)).scalars().unique().all()
    return {
        "tool": "search_open_projects",
        "source": "afridev-hub://projects",
        "count": len(projects),
        "results": [
            {
                "id": str(project.id),
                "name": project.name,
                "slug": project.slug,
                "description": project.description[:400],
                "technologies": project.technologies,
                "country": project.country.code if project.country else None,
                "repository_url": project.repository_url,
                "creator": project.creator.username,
            }
            for project in projects
        ],
    }
