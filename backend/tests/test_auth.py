"""Health, authentication, CSRF and profile tests."""

import pytest

from tests.conftest import login, set_country


@pytest.mark.asyncio
async def test_health_endpoints(client):
    root = await client.get("/")
    assert root.status_code == 200
    assert root.json()["slogan"] == "Show. Solve. Prove."

    health = await client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_dev_login_creates_session(client):
    user = await login(client, "amina-test")
    assert user["username"] == "amina-test"

    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "amina-test"

    logout = await client.post("/api/v1/auth/logout")
    assert logout.status_code == 204
    assert (await client.get("/api/v1/auth/me")).status_code == 401


@pytest.mark.asyncio
async def test_profile_update_sets_country_and_skills(client):
    await login(client, "profil-test")
    profile = await set_country(client, "CM")
    assert profile["country"]["code"] == "CM"

    response = await client.patch(
        "/api/v1/users/me",
        json={"bio": "Backend developer", "skills": ["Python", "PostgreSQL"], "roles": ["developer", "sponsor"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["bio"] == "Backend developer"
    assert {skill["name"] for skill in body["skills"]} == {"Python", "PostgreSQL"}


@pytest.mark.asyncio
async def test_csrf_required_for_authenticated_mutations(client):
    await login(client, "csrf-test")
    client.headers.pop("X-CSRF-Token", None)
    blocked = await client.post(
        "/api/v1/projects",
        json={"name": "No CSRF", "description": "x" * 40, "collaboration_mode": "showcase"},
    )
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "csrf_failed"


@pytest.mark.asyncio
async def test_protected_endpoints_require_authentication(client):
    assert (await client.get("/api/v1/projects/discover")).status_code == 200
    assert (await client.get("/api/v1/conversations")).status_code == 401
    assert (await client.get("/api/v1/admin/overview")).status_code == 401


@pytest.mark.asyncio
async def test_admin_endpoints_forbidden_for_regular_user(client):
    await login(client, "not-admin")
    response = await client.get("/api/v1/admin/overview")
    assert response.status_code == 403
