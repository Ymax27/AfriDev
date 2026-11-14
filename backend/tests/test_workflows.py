"""End-to-end workflow tests: projects, contributions, knowledge, reputation."""

import pytest
from sqlalchemy import func, select

from app.modules.reputation.models import ReputationTransaction
from tests.conftest import create_project, login, set_country


@pytest.mark.asyncio
async def test_project_creation_and_discovery_excludes_interactions(client):
    await login(client, "creator-one")
    project = await create_project(client, name="Discovery Target")

    await login(client, "viewer-one")
    feed = await client.get("/api/v1/projects/discover")
    assert feed.status_code == 200
    ids = [item["id"] for item in feed.json()["items"]]
    assert project["id"] in ids

    passed = await client.post(f"/api/v1/projects/{project['id']}/pass")
    assert passed.status_code == 204
    feed_after = await client.get("/api/v1/projects/discover")
    assert project["id"] not in [item["id"] for item in feed_after.json()["items"]]

    liked = await client.post(f"/api/v1/projects/{project['id']}/like")
    assert liked.status_code == 204
    detail = await client.get(f"/api/v1/projects/{project['id']}")
    assert detail.json()["liked_by_me"] is True
    assert detail.json()["likes_count"] == 1


@pytest.mark.asyncio
async def test_project_filters_by_country_and_technology(client):
    await login(client, "filter-owner")
    await create_project(client, name="Cameroon Fintech", country_code="CM", technologies=["Flutter"])

    filtered = await client.get("/api/v1/projects", params={"country": "CM", "technology": "flutter"})
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1


@pytest.mark.asyncio
async def test_contribution_acceptance_creates_private_conversation(client):
    await login(client, "maintainer")
    project = await create_project(client, name="Collab Project")

    await login(client, "contributor")
    request = await client.post(
        f"/api/v1/projects/{project['id']}/contributions",
        json={"message": "I can help with documentation and tests for this project.", "domain": "documentation"},
    )
    assert request.status_code == 201, request.text
    request_id = request.json()["id"]

    # The requester cannot read the maintainer's queue.
    forbidden = await client.get(f"/api/v1/projects/{project['id']}/contributions")
    assert forbidden.status_code == 403
    before = await client.get("/api/v1/conversations")
    assert before.json()["total"] == 0

    await login(client, "maintainer")
    accepted = await client.post(f"/api/v1/contributions/{request_id}/accept")
    assert accepted.status_code == 200
    conversation_id = accepted.json()["conversation_id"]
    assert conversation_id

    await login(client, "contributor")
    conversations = await client.get("/api/v1/conversations")
    assert conversations.json()["total"] == 1
    messages = await client.get(f"/api/v1/conversations/{conversation_id}/messages")
    assert messages.status_code == 200
    assert messages.json()

    await login(client, "outsider")
    denied = await client.get(f"/api/v1/conversations/{conversation_id}/messages")
    assert denied.status_code == 403


@pytest.mark.asyncio
async def test_accepted_solution_creates_field_report_and_awards_points(client, db):
    await login(client, "problem-author")
    await set_country(client, "CM")
    problem = await client.post(
        "/api/v1/knowledge",
        json={
            "title": "Orange Money callback signature never validates",
            "description": "We receive callbacks but the HMAC signature never matches our computed digest.",
            "category": "payments",
            "technology": "Python",
            "country_code": "CM",
        },
    )
    assert problem.status_code == 201, problem.text
    problem_id = problem.json()["id"]

    await login(client, "solver")
    solution = await client.post(
        f"/api/v1/knowledge/{problem_id}/solutions",
        json={"explanation": "Hash the raw request body bytes before JSON decoding and compare in constant time."},
    )
    assert solution.status_code == 201, solution.text
    solution_id = solution.json()["id"]

    # A solver cannot accept their own solution.
    self_accept = await client.post(f"/api/v1/knowledge/{problem_id}/solutions/{solution_id}/accept")
    assert self_accept.status_code == 403

    await login(client, "problem-author")
    accepted = await client.post(f"/api/v1/knowledge/{problem_id}/solutions/{solution_id}/accept")
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["is_accepted"] is True

    reports = await client.get("/api/v1/field-reports", params={"country": "CM"})
    assert reports.json()["total"] == 1
    report = reports.json()["items"][0]
    assert report["solution_id"] == solution_id
    assert report["problem_summary"].startswith("We receive callbacks")

    leaderboard = await client.get("/api/v1/leaderboard/developers")
    solver = next(item for item in leaderboard.json()["items"] if item["username"] == "solver")
    assert solver["reputation_points"] == 20
    solver_level = solver["level"]
    assert solver_level == "newcomer"

    rows = (
        await db.execute(
            select(func.count(ReputationTransaction.id)).where(
                ReputationTransaction.action_type == "accepted_solution"
            )
        )
    ).scalar_one()
    assert rows == 1


@pytest.mark.asyncio
async def test_duplicate_acceptance_does_not_double_award(client, db):
    await login(client, "dup-author")
    problem = await client.post(
        "/api/v1/knowledge",
        json={
            "title": "Duplicate award guard on accepted solutions",
            "description": "The same solution must never generate two reputation transactions.",
            "category": "backend",
        },
    )
    problem_id = problem.json()["id"]

    await login(client, "dup-solver")
    first = await client.post(
        f"/api/v1/knowledge/{problem_id}/solutions",
        json={"explanation": "First solution explanation that is long enough to satisfy validation."},
    )
    second = await client.post(
        f"/api/v1/knowledge/{problem_id}/solutions",
        json={"explanation": "Second solution explanation that is long enough to satisfy validation."},
    )

    await login(client, "dup-author")
    await client.post(f"/api/v1/knowledge/{problem_id}/solutions/{first.json()['id']}/accept")
    conflict = await client.post(f"/api/v1/knowledge/{problem_id}/solutions/{second.json()['id']}/accept")
    assert conflict.status_code == 409

    count = (
        await db.execute(
            select(func.count(ReputationTransaction.id)).where(
                ReputationTransaction.action_type == "accepted_solution"
            )
        )
    ).scalar_one()
    assert count == 1


@pytest.mark.asyncio
async def test_field_report_confirmation_requires_same_country(client, db):
    await login(client, "report-author")
    await set_country(client, "CM")
    problem = await client.post(
        "/api/v1/knowledge",
        json={
            "title": "Field report confirmation country rule",
            "description": "Only developers from the report country should be able to confirm knowledge.",
            "category": "payments",
            "country_code": "CM",
        },
    )
    problem_id = problem.json()["id"]

    await login(client, "report-solver")
    await set_country(client, "CM")
    solution = await client.post(
        f"/api/v1/knowledge/{problem_id}/solutions",
        json={"explanation": "Apply the documented retry policy and validate webhook signatures."},
    )
    await login(client, "report-author")
    await client.post(f"/api/v1/knowledge/{problem_id}/solutions/{solution.json()['id']}/accept")

    reports = await client.get("/api/v1/field-reports", params={"country": "CM"})
    report_id = reports.json()["items"][0]["id"]

    await login(client, "kenyan-dev")
    await set_country(client, "KE")
    blocked = await client.post(f"/api/v1/field-reports/{report_id}/confirm", json={})
    assert blocked.status_code == 403

    await login(client, "cameroonian-dev")
    await set_country(client, "CM")
    confirmed = await client.post(f"/api/v1/field-reports/{report_id}/confirm", json={"comment": "Validé"})
    assert confirmed.status_code == 201
    assert confirmed.json()["confirmation_count"] == 1

    duplicate = await client.post(f"/api/v1/field-reports/{report_id}/confirm", json={})
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_country_hub_and_leaderboards_render(client):
    await login(client, "hub-user")
    await set_country(client, "GH")
    await create_project(client, name="Ghana Hub Project", country_code="GH")

    hub = await client.get("/api/v1/countries/GH")
    assert hub.status_code == 200
    body = hub.json()
    assert body["country"]["code"] == "GH"
    assert body["stats"]["developers"] >= 1
    assert body["stats"]["projects"] >= 1

    assert (await client.get("/api/v1/leaderboard/developers")).status_code == 200
    assert (await client.get("/api/v1/leaderboard/projects")).status_code == 200
    assert (await client.get("/api/v1/leaderboard/countries")).status_code == 200


@pytest.mark.asyncio
async def test_api_directory_and_mcp_public_tools(client, db):
    from app.modules.api_directory.models import APIEntry

    await login(client, "api-admin", as_admin=True)
    # The directory is curated: providers edit their sheet, nobody creates entries through the API.
    read_only = await client.post(
        "/api/v1/apis",
        json={"name": "Blocked", "provider_name": "Blocked", "category": "payments"},
    )
    assert read_only.status_code == 405

    entry = APIEntry(
        name="Test Payments API",
        provider_name="Test Provider",
        slug="test-payments-api",
        description="A payments API used to verify directory behaviour.",
        category="payments",
        countries=["CM", "NG"],
        documentation_url="https://docs.example.com",
    )
    db.add(entry)
    await db.commit()

    directory = await client.get("/api/v1/apis", params={"q": "payments"})
    assert directory.json()["total"] == 1

    updated = await client.patch(f"/api/v1/apis/{entry.id}", json={"pricing": "Free tier"})
    assert updated.status_code == 200, updated.text
    assert updated.json()["pricing"] == "Free tier"

    from app.mcp.tools.search_api_directory import search_api_directory
    from app.mcp.tools.search_field_reports import search_field_reports
    from app.mcp.tools.search_open_projects import search_open_projects

    api_results = await search_api_directory(db, query="payments", limit=5)
    assert api_results["count"] == 1
    assert api_results["source"] == "afridev-hub://api-directory"

    project_results = await search_open_projects(db, limit=5)
    assert project_results["tool"] == "search_open_projects"

    report_results = await search_field_reports(db, country="CM", limit=5)
    assert report_results["tool"] == "search_field_reports"


@pytest.mark.asyncio
async def test_useful_solution_votes_award_two_points_capped_at_ten(client, db):
    from datetime import UTC, datetime, timedelta

    from app.modules.users.models import User

    await login(client, "vote-author")
    problem = await client.post(
        "/api/v1/knowledge",
        json={
            "title": "Useful vote accounting across the community",
            "description": "Community votes should award two points each and stop at ten per solution.",
            "category": "backend",
        },
    )
    problem_id = problem.json()["id"]
    await login(client, "vote-solver")
    solution_id = (
        await client.post(
            f"/api/v1/knowledge/{problem_id}/solutions",
            json={"explanation": "A complete explanation long enough for the schema to accept it."},
        )
    ).json()["id"]

    # A brand-new account may vote, but its vote does not move the ledger yet.
    await login(client, "fresh-voter")
    first = await client.post(f"/api/v1/knowledge/solutions/{solution_id}/vote")
    assert first.status_code == 201, first.text
    assert first.json()["useful_votes"] == 1
    reputation = await client.get("/api/v1/reputation/me")
    assert reputation.status_code == 200

    # Self-votes are refused.
    await login(client, "vote-solver")
    assert (await client.post(f"/api/v1/knowledge/solutions/{solution_id}/vote")).status_code == 403

    # Seasoned voters award two points each, up to the ten-point cap.
    for index in range(6):
        await login(client, f"seasoned-voter-{index}")
        row = (
            await db.execute(select(User).where(User.username == f"seasoned-voter-{index}"))
        ).scalar_one()
        row.created_at = datetime.now(UTC) - timedelta(days=30)
        await db.commit()
        voted = await client.post(f"/api/v1/knowledge/solutions/{solution_id}/vote")
        assert voted.status_code == 201, voted.text

    await login(client, "vote-solver")
    detail = await client.get("/api/v1/reputation/me")
    assert detail.json()["reputation_points"] == 10


@pytest.mark.asyncio
async def test_country_cup_uses_weekly_average_per_active_member(client):
    await login(client, "cup-dev")
    response = await client.get("/api/v1/leaderboard/countries")
    assert response.status_code == 200
    for item in response.json():
        assert item["period"] == "week"
        assert "week_points" in item
        assert item["average_points"] >= 0


@pytest.mark.asyncio
async def test_mission_submission_and_sponsor_review(client):
    await login(client, "sponsor-user")
    mission = await client.post(
        "/api/v1/missions",
        json={
            "title": "Integrate a mobile money sandbox",
            "description": "Build a reference integration with tests and documentation for local merchants.",
            "objectives": "Ship a working sandbox flow with reconciliation notes.",
            "required_skills": ["Python"],
            "reward_points": 30,
        },
    )
    assert mission.status_code == 403  # sponsors need the sponsor role

    await client.patch("/api/v1/users/me", json={"roles": ["developer", "sponsor"]})
    mission = await client.post(
        "/api/v1/missions",
        json={
            "title": "Integrate a mobile money sandbox",
            "description": "Build a reference integration with tests and documentation for local merchants.",
            "objectives": "Ship a working sandbox flow with reconciliation notes.",
            "required_skills": ["Python"],
            "reward_points": 30,
        },
    )
    assert mission.status_code == 201, mission.text
    mission_id = mission.json()["id"]

    await login(client, "mission-dev")
    submission = await client.post(
        f"/api/v1/missions/{mission_id}/submissions",
        json={"summary": "Integration published with sandbox tests and a short field note."},
    )
    assert submission.status_code == 201, submission.text
    submission_id = submission.json()["id"]

    await login(client, "sponsor-user")
    review = await client.post(
        f"/api/v1/missions/submissions/{submission_id}/review",
        json={"approve": True, "review_note": "Excellent work"},
    )
    assert review.status_code == 200
    assert review.json()["points_awarded"] == 30

    await login(client, "mission-dev")
    reputation = await client.get("/api/v1/reputation/me")
    assert reputation.json()["reputation_points"] == 30
