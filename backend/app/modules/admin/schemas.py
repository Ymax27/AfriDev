"""Admin dashboard schemas."""

from uuid import UUID

from pydantic import BaseModel


class AdminOverview(BaseModel):
    users: int
    active_users: int
    demo_users: int
    projects: int
    problems: int
    field_reports: int
    missions: int
    api_entries: int
    open_reports: int
    reputation_transactions: int
    points_awarded: int


class AdminUserOut(BaseModel):
    id: UUID
    username: str
    full_name: str | None = None
    is_active: bool
    is_admin: bool
    is_demo: bool
    reputation_points: int
    level: str
    reputation_frozen: bool
    country_code: str | None = None


class AdminUserListOut(BaseModel):
    items: list[AdminUserOut]
    total: int
    page: int
    page_size: int
