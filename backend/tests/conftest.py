"""Test fixtures: isolated SQLite database, app client and helpers."""

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.rate_limit import reset_rate_limits
from app.main import app
from app.models import *  # noqa: F401,F403 - ensure all tables are registered


@pytest_asyncio.fixture
async def engine(tmp_path):
    database_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
    engine = create_async_engine(database_url)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db(session_factory) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(session_factory) -> AsyncIterator[AsyncClient]:
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    reset_rate_limits()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        yield http_client
    app.dependency_overrides.clear()


async def login(client: AsyncClient, username: str = "tester", *, as_admin: bool = False) -> dict:
    response = await client.post(
        "/api/v1/auth/dev-login", json={"username": username, "as_admin": as_admin}
    )
    assert response.status_code == 200, response.text
    client.headers["X-CSRF-Token"] = client.cookies.get("afridev_csrf", "")
    return response.json()


async def set_country(client: AsyncClient, code: str) -> dict:
    response = await client.patch("/api/v1/users/me", json={"country_code": code})
    assert response.status_code == 200, response.text
    return response.json()


async def create_project(client: AsyncClient, **overrides) -> dict:
    payload = {
        "name": "Test Project",
        "description": "A project used by the automated test suite to verify discovery behaviour.",
        "technologies": ["Python", "FastAPI"],
        "tags": ["test"],
        "category": "web",
        "collaboration_mode": "open_to_contributors",
    }
    payload.update(overrides)
    response = await client.post("/api/v1/projects", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


@pytest_asyncio.fixture(autouse=True)
async def reference_countries(session_factory):
    """Every test database starts with the reference country list."""
    from app.modules.countries.models import Country

    async with session_factory() as session:
        for code, name, name_fr, flag in [
            ("CM", "Cameroon", "Cameroun", "\U0001F1E8\U0001F1F2"),
            ("NG", "Nigeria", "Nigéria", "\U0001F1F3\U0001F1EC"),
            ("KE", "Kenya", "Kenya", "\U0001F1F0\U0001F1EA"),
            ("GH", "Ghana", "Ghana", "\U0001F1EC\U0001F1ED"),
            ("SN", "Senegal", "Sénégal", "\U0001F1F8\U0001F1F3"),
            ("CI", "Côte d'Ivoire", "Côte d'Ivoire", "\U0001F1E8\U0001F1EE"),
            ("ZA", "South Africa", "Afrique du Sud", "\U0001F1FF\U0001F1E6"),
            ("RW", "Rwanda", "Rwanda", "\U0001F1F7\U0001F1FC"),
        ]:
            session.add(Country(code=code, name=name, name_fr=name_fr, flag_emoji=flag))
        await session.commit()
    yield


@pytest.fixture(autouse=True)
def _reset_limits() -> None:
    reset_rate_limits()
