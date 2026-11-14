"""AfriDev Hub — FastAPI application entrypoint."""

import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.security import csrf_tokens_match
from app.websocket.routes import router as websocket_router

configure_logging(settings.log_level)
logger = logging.getLogger("afridev.api")

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
CSRF_EXEMPT_PATHS = {
    f"{settings.api_v1_prefix}/auth/dev-login",
    f"{settings.api_v1_prefix}/auth/github/callback",
}


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "starting %s in %s mode", settings.app_name, settings.app_env,
        extra={"path": "startup", "status_code": 200},
    )
    try:
        from app.modules.field_reports.service import flag_stale_reports

        async with SessionLocal() as session:
            flagged = await flag_stale_reports(session)
        if flagged:
            logger.info("field reports flagged for revalidation: %s", flagged)
    except Exception:  # pragma: no cover - startup must not fail on a maintenance pass
        logger.exception("field report revalidation pass failed")
    yield
    logger.info("shutting down", extra={"path": "shutdown", "status_code": 200})


app = FastAPI(
    title="AfriDev Hub API",
    description=(
        "Show. Solve. Prove. API for the African developer knowledge, project discovery "
        "and verifiable reputation platform."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"http://localhost:\d+|http://127\.0\.0\.1:\d+",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def observability_and_security(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    logger.info(
        "%s %s -> %s in %sms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "user_id": getattr(request.state, "user_id", None),
        },
    )
    return response


@app.middleware("http")
async def csrf_protection(request: Request, call_next):
    """Double-submit cookie CSRF check for cookie-authenticated mutations."""
    needs_check = (
        request.method not in SAFE_METHODS
        and request.url.path.startswith("/api/")
        and request.url.path not in CSRF_EXEMPT_PATHS
        and settings.session_cookie_name in request.cookies
    )
    if needs_check:
        cookie_token = request.cookies.get(settings.csrf_cookie_name)
        header_token = request.headers.get("X-CSRF-Token")
        if not csrf_tokens_match(cookie_token, header_token):
            return JSONResponse(
                status_code=403,
                content={"error": {"code": "csrf_failed", "message": "Missing or invalid CSRF token"}},
            )
    return await call_next(request)


register_exception_handlers(app)


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {
        "name": "AfriDev Hub API",
        "slogan": "Show. Solve. Prove.",
        "docs": "/docs",
        "api": settings.api_v1_prefix,
    }


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env, "version": "0.1.0"}


@app.get(f"{settings.api_v1_prefix}/health", tags=["meta"])
async def api_health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env, "version": "0.1.0"}


@app.get(f"{settings.api_v1_prefix}/health/db", tags=["meta"])
async def database_health() -> JSONResponse:
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - depends on infrastructure
        logger.exception("database health check failed")
        return JSONResponse(status_code=503, content={"status": "unavailable", "detail": str(exc)})
    return JSONResponse(content={"status": "ok", "database": "reachable"})


app.include_router(api_router, prefix=settings.api_v1_prefix)
app.include_router(websocket_router)
