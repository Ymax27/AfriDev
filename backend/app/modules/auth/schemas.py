"""Authentication schemas."""

from pydantic import BaseModel, Field


class AuthorizationUrlOut(BaseModel):
    authorization_url: str
    state: str


class DevLoginRequest(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=40)
    as_admin: bool = False


class AuthStatusOut(BaseModel):
    authenticated: bool
    github_oauth_enabled: bool
    demo_mode: bool
