"""Centralised application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AfriDev Hub API"
    app_env: Literal["development", "test", "production"] = "development"
    api_v1_prefix: str = "/api/v1"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://afridev:afridev@localhost:5432/afridev"
    secret_key: str = "change-me-in-production-please-use-a-long-random-value"
    session_cookie_name: str = "afridev_session"
    session_max_age_seconds: int = 60 * 60 * 24 * 7
    csrf_cookie_name: str = "afridev_csrf"
    cookie_secure: bool | None = None
    cookie_domain: str | None = None

    github_client_id: str | None = None
    github_client_secret: str | None = None
    github_callback_url: str = "http://localhost:8000/api/v1/auth/github/callback"

    frontend_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    demo_mode: bool = True
    min_github_account_age_days: int = 30
    field_report_revalidation_days: int = 90

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def secure_cookies(self) -> bool:
        if self.cookie_secure is None:
            return self.is_production
        return self.cookie_secure

    @property
    def github_oauth_enabled(self) -> bool:
        return bool(self.github_client_id and self.github_client_secret)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
