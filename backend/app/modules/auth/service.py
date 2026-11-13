"""GitHub OAuth and local session provisioning."""

import logging
import re
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ForbiddenError, UnauthorizedError, ValidationError
from app.core.security import generate_oauth_state, pkce_challenge
from app.modules.users.models import User, UserRole, UserSkill

logger = logging.getLogger("afridev.auth")

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_URL = "https://api.github.com"


async def exchange_code_for_token(code: str, code_verifier: str) -> str:
    payload = {
        "client_id": settings.github_client_id,
        "client_secret": settings.github_client_secret,
        "code": code,
        "redirect_uri": settings.github_callback_url,
        "code_verifier": code_verifier,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            GITHUB_TOKEN_URL, data=payload, headers={"Accept": "application/json"}
        )
    response.raise_for_status()
    data = response.json()
    token = data.get("access_token")
    if not token:
        raise UnauthorizedError(f"GitHub did not return an access token: {data.get('error')}")
    return str(token)


async def fetch_github_profile(access_token: str) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"}
    async with httpx.AsyncClient(timeout=15) as client:
        user_response = await client.get(f"{GITHUB_API_URL}/user", headers=headers)
        user_response.raise_for_status()
        profile = user_response.json()
        if not profile.get("email"):
            email_response = await client.get(f"{GITHUB_API_URL}/user/emails", headers=headers)
            if email_response.status_code == 200:
                for email in email_response.json():
                    if email.get("primary") and email.get("verified"):
                        profile["email"] = email["email"]
                        break
    return profile


def _normalise_username(raw: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]", "", raw)[:40]
    return cleaned or f"dev-{secrets.token_hex(3)}"


def _parse_github_created_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


async def _unique_username(db: AsyncSession, base: str) -> str:
    candidate = _normalise_username(base)
    suffix = 1
    while True:
        exists = await db.execute(
            select(User.id).where(func.lower(User.username) == candidate.lower()).limit(1)
        )
        if exists.scalar_one_or_none() is None:
            return candidate
        suffix += 1
        candidate = f"{_normalise_username(base)[:35]}-{suffix}"


async def upsert_github_user(db: AsyncSession, profile: dict[str, Any]) -> User:
    github_id = int(profile["id"])
    created_at = _parse_github_created_at(profile.get("created_at"))
    if created_at and created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    if created_at:
        age = datetime.now(UTC) - created_at
        if age < timedelta(days=settings.min_github_account_age_days):
            raise ForbiddenError(
                "GitHub accounts younger than "
                f"{settings.min_github_account_age_days} days cannot authenticate"
            )

    user = (
        await db.execute(select(User).where(User.github_id == github_id))
    ).scalar_one_or_none()
    login = profile.get("login") or f"github-{github_id}"

    if user is None:
        user = User(
            github_id=github_id,
            github_login=login,
            username=await _unique_username(db, login),
            email=profile.get("email"),
            full_name=profile.get("name"),
            avatar_url=profile.get("avatar_url"),
            bio=profile.get("bio"),
            city=profile.get("location"),
            website_url=profile.get("blog") or None,
            github_url=profile.get("html_url"),
            github_created_at=created_at,
            last_login_at=datetime.now(UTC),
        )
        user.roles = [UserRole(role="developer")]
        db.add(user)
        await db.flush()
        await give_expertise_defaults(db, user)
        logger.info("created user from GitHub", extra={"user_id": str(user.id)})
    else:
        user.github_login = login
        user.avatar_url = profile.get("avatar_url") or user.avatar_url
        user.full_name = profile.get("name") or user.full_name
        user.email = profile.get("email") or user.email
        user.github_created_at = created_at or user.github_created_at
        user.last_login_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(user, attribute_names=["roles", "skills", "country"])
    return user


async def give_expertise_defaults(db: AsyncSession, user: User) -> None:
    """Add starter skills. Only called for freshly created accounts."""
    db.add(UserSkill(user_id=user.id, name="TypeScript", level="intermediate"))
    await db.flush()


async def dev_login(db: AsyncSession, username: str | None, as_admin: bool) -> User:
    """Local-only authentication used when GitHub OAuth is not configured."""

    if settings.is_production or not settings.demo_mode:
        raise ForbiddenError("Development login is disabled in this environment")

    if username:
        candidate = _normalise_username(username)
        user = (
            await db.execute(select(User).where(func.lower(User.username) == candidate.lower()))
        ).scalar_one_or_none()
    else:
        user = None
        candidate = f"dev-{secrets.token_hex(3)}"

    if user is None:
        user = User(
            username=await _unique_username(db, candidate),
            full_name=candidate.replace("-", " ").title(),
            avatar_url=None,
            bio="Local development account",
            is_demo=not as_admin,
            last_login_at=datetime.now(UTC),
        )
        if as_admin:
            user.is_admin = True
            user.roles = [UserRole(role="developer"), UserRole(role="admin")]
        else:
            user.roles = [UserRole(role="developer")]
        db.add(user)
        await db.flush()
        await give_expertise_defaults(db, user)

    user.last_login_at = datetime.now(UTC)
    if as_admin and not user.is_admin:
        user.is_admin = True
        user.roles.append(UserRole(role="admin"))
    await db.commit()
    await db.refresh(user, attribute_names=["roles", "skills", "country"])
    return user


def build_authorization_url(state: str) -> tuple[str, str]:
    verifier = secrets.token_urlsafe(48)
    params = {
        "client_id": settings.github_client_id or "",
        "redirect_uri": settings.github_callback_url,
        "scope": "read:user user:email",
        "state": state,
        "code_challenge": pkce_challenge(verifier),
        "code_challenge_method": "S256",
    }
    query = "&".join(f"{key}={httpx.QueryParams({key: value})[key]}" for key, value in params.items())
    return f"{GITHUB_AUTHORIZE_URL}?{query}", verifier


def new_oauth_state() -> str:
    return generate_oauth_state()


def validate_dev_username(value: str) -> str:
    if not re.fullmatch(r"[a-zA-Z0-9_-]{3,40}", value):
        raise ValidationError("Username must be 3-40 characters of letters, numbers, - or _")
    return value
