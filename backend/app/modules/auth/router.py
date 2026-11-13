"""Authentication endpoints: GitHub OAuth, session and logout."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.responses import RedirectResponse

from app.api.dependencies import CurrentUser, DbSession, OptionalUser
from app.core.config import settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.rate_limit import rate_limit
from app.core.security import generate_csrf_token, read_session_token
from app.modules.auth import service
from app.modules.auth.schemas import AuthorizationUrlOut, AuthStatusOut, DevLoginRequest
from app.modules.users.schemas import UserOut

logger = logging.getLogger("afridev.auth")
router = APIRouter(prefix="/auth", tags=["auth"])

OAUTH_STATE_COOKIE = "afridev_oauth_state"
OAUTH_VERIFIER_COOKIE = "afridev_oauth_verifier"


def set_session_cookies(response: Response, user_id) -> None:
    from app.core.security import create_session_token

    response.set_cookie(
        settings.session_cookie_name,
        create_session_token(user_id),
        max_age=settings.session_max_age_seconds,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
        domain=settings.cookie_domain,
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        generate_csrf_token(),
        max_age=settings.session_max_age_seconds,
        httponly=False,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
        domain=settings.cookie_domain,
    )


def clear_session_cookies(response: Response) -> None:
    response.delete_cookie(settings.session_cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")


@router.get("/status", response_model=AuthStatusOut)
async def auth_status() -> AuthStatusOut:
    return AuthStatusOut(
        authenticated=False,
        github_oauth_enabled=settings.github_oauth_enabled,
        demo_mode=settings.demo_mode and not settings.is_production,
    )


@router.get("/github", response_model=AuthorizationUrlOut)
async def github_authorize(response: Response) -> AuthorizationUrlOut:
    if not settings.github_oauth_enabled:
        raise ForbiddenError(
            "GitHub OAuth is not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET."
        )
    state = service.new_oauth_state()
    url, verifier = service.build_authorization_url(state)
    response.set_cookie(
        OAUTH_STATE_COOKIE, state, max_age=600, httponly=True, secure=settings.secure_cookies, samesite="lax", path="/"
    )
    response.set_cookie(
        OAUTH_VERIFIER_COOKIE,
        verifier,
        max_age=600,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )
    return AuthorizationUrlOut(authorization_url=url, state=state)


@router.get("/github/callback")
async def github_callback(
    request: Request,
    db: DbSession,
    code: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    frontend = settings.frontend_url.rstrip("/")
    if error:
        return RedirectResponse(f"{frontend}/login?error={error}")
    cookie_state = request.cookies.get(OAUTH_STATE_COOKIE)
    verifier = request.cookies.get(OAUTH_VERIFIER_COOKIE)
    if not code or not state or not cookie_state or not verifier or state != cookie_state:
        return RedirectResponse(f"{frontend}/login?error=invalid_state")
    try:
        token = await service.exchange_code_for_token(code, verifier)
        profile = await service.fetch_github_profile(token)
        user = await service.upsert_github_user(db, profile)
    except (ForbiddenError, UnauthorizedError) as exc:
        logger.warning("github login rejected: %s", exc.message)
        return RedirectResponse(f"{frontend}/login?error=github_rejected")
    except Exception:
        logger.exception("github login failed")
        return RedirectResponse(f"{frontend}/login?error=github_unavailable")

    redirect = RedirectResponse(f"{frontend}/dashboard")
    set_session_cookies(redirect, user.id)
    redirect.delete_cookie(OAUTH_STATE_COOKIE, path="/")
    redirect.delete_cookie(OAUTH_VERIFIER_COOKIE, path="/")
    return redirect


@router.post(
    "/dev-login",
    response_model=UserOut,
    dependencies=[Depends(rate_limit(20, 60, scope="dev-login"))],
)
async def dev_login(payload: DevLoginRequest, response: Response, db: DbSession) -> UserOut:
    username = service.validate_dev_username(payload.username) if payload.username else None
    user = await service.dev_login(db, username, payload.as_admin)
    set_session_cookies(response, user.id)
    return UserOut.model_validate(user)


@router.get("/me", response_model=UserOut)
async def read_session_user(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.get("/me/optional", response_model=UserOut | None)
async def read_optional_user(user: OptionalUser) -> UserOut | None:
    return UserOut.model_validate(user) if user else None


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response) -> None:
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        read_session_token(token)
    clear_session_cookies(response)
