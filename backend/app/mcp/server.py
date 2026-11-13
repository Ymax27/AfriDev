"""Read-only MCP server exposing three public search tools.

Public information only: no private messages, emails or personal data.
"""

from typing import Any

from app.core.database import SessionLocal
from app.mcp.tools.search_api_directory import search_api_directory
from app.mcp.tools.search_field_reports import search_field_reports
from app.mcp.tools.search_open_projects import search_open_projects

TOOL_REGISTRY = {
    "search_field_reports": search_field_reports,
    "search_open_projects": search_open_projects,
    "search_api_directory": search_api_directory,
}


async def call_tool(name: str, **arguments: Any) -> dict[str, Any]:
    if name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown MCP tool: {name}")
    async with SessionLocal() as db:
        return await TOOL_REGISTRY[name](db, **arguments)


def build_server():
    """Build a FastMCP server when the optional MCP SDK is installed."""
    from mcp.server.fastmcp import FastMCP

    server = FastMCP("afridev-hub")

    @server.tool()
    async def search_field_reports_tool(query: str = "", country: str | None = None, limit: int = 10) -> dict:
        """Search validated field knowledge from African developers."""
        return await call_tool("search_field_reports", query=query, country=country, limit=limit)

    @server.tool()
    async def search_open_projects_tool(query: str = "", country: str | None = None, limit: int = 10) -> dict:
        """Discover published projects that accept new contributors."""
        return await call_tool("search_open_projects", query=query, country=country, limit=limit)

    @server.tool()
    async def search_api_directory_tool(
        query: str = "", category: str | None = None, country: str | None = None, limit: int = 10
    ) -> dict:
        """Retrieve public African API directory entries."""
        return await call_tool("search_api_directory", query=query, category=category, country=country, limit=limit)

    return server


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
