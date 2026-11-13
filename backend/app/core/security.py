"""Session cookie signing, CSRF tokens and OAuth state helpers."""

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.config import settings

_serializer = URLSafeTimedSerializer(settings.secret_key, salt="afridev-session")


def create_session_token(user_id: UUID) -> str:
    return _serializer.dumps({"sub": str(user_id)})


def read_session_token(token: str) -> UUID | None:
    try:
        payload = _serializer.loads(token, max_age=settings.session_max_age_seconds)
    except (BadSignature, SignatureExpired):
        return None
    try:
        return UUID(payload["sub"])
    except (KeyError, ValueError):
        return None


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def csrf_tokens_match(cookie_value: str | None, header_value: str | None) -> bool:
    if not cookie_value or not header_value:
        return False
    return hmac.compare_digest(cookie_value.encode(), header_value.encode())


def generate_oauth_state() -> str:
    return secrets.token_urlsafe(24)


def pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def oauth_state_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(minutes=10)
