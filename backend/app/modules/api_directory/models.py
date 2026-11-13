"""African API provider and API catalogue entries."""

from uuid import UUID

from sqlalchemy import JSON, Boolean, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class APIProvider(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "api_providers"

    owner_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    website_url: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class APIEntry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "api_entries"

    provider_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("api_providers.id", ondelete="SET NULL"), index=True
    )
    owner_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    provider_name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    countries: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    documentation_url: Mapped[str] = mapped_column(String(500), nullable=False)
    pricing: Mapped[str | None] = mapped_column(String(255))
    api_status: Mapped[str] = mapped_column(String(30), default="operational", nullable=False)
    integration_notes: Mapped[str | None] = mapped_column(Text)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
