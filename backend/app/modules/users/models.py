"""User accounts, roles, skills and blocking relationships."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    github_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, index=True)
    github_login: Mapped[str | None] = mapped_column(String(80))
    github_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    full_name: Mapped[str | None] = mapped_column(String(120))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    bio: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(String(120))
    website_url: Mapped[str | None] = mapped_column(String(500))
    github_url: Mapped[str | None] = mapped_column(String(500))
    country_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("countries.id", ondelete="SET NULL"))
    reputation_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(20), default="newcomer", nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    reputation_frozen: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    country = relationship("Country", lazy="selectin")
    roles = relationship("UserRole", lazy="selectin", cascade="all, delete-orphan", back_populates="user")
    skills = relationship("UserSkill", lazy="selectin", cascade="all, delete-orphan", back_populates="user")


class UserRole(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role", name="uq_user_roles_user_role"),)

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    user = relationship("User", back_populates="roles")


class UserSkill(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_skills"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_user_skills_user_name"),)

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    level: Mapped[str] = mapped_column(String(20), default="intermediate", nullable=False)
    years_experience: Mapped[int | None] = mapped_column(Integer)
    user = relationship("User", back_populates="skills")


class UserBlock(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_blocks"
    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="uq_user_blocks_pair"),
        Index("ix_user_blocks_blocked_id", "blocked_id"),
    )

    blocker_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    blocked_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    reason: Mapped[str | None] = mapped_column(String(255))
