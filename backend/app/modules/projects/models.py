"""Projects, discovery interactions, feedback and ownership verification."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
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
from app.core.enums import CollaborationMode, VerificationStatus


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_country_mode", "country_id", "collaboration_mode"),
        CheckConstraint("github_stars >= 0", name="github_stars_non_negative"),
    )

    creator_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    country_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("countries.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    cover_image_url: Mapped[str | None] = mapped_column(String(500))
    repository_url: Mapped[str | None] = mapped_column(String(500))
    demo_url: Mapped[str | None] = mapped_column(String(500))
    technologies: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False, default="web")
    collaboration_mode: Mapped[str] = mapped_column(
        String(30), default=CollaborationMode.SHOWCASE.value, nullable=False, index=True
    )
    ownership_status: Mapped[str] = mapped_column(
        String(20), default=VerificationStatus.PENDING.value, nullable=False
    )
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    github_stars: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    creator = relationship("User", lazy="selectin")
    country = relationship("Country", lazy="selectin")


class ProjectLike(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "project_likes"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_likes_project_user"),)

    project_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ProjectPass(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "project_passes"
    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_passes_project_user"),)

    project_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ProjectFeedback(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "project_feedback"
    __table_args__ = (UniqueConstraint("project_id", "author_id", name="uq_project_feedback_project_author"),)

    project_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    author_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    concept_answer: Mapped[str] = mapped_column(Text, nullable=False)
    improvement_answer: Mapped[str] = mapped_column(Text, nullable=False)
    feature_answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_useful: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    author = relationship("User", lazy="selectin")


class OwnershipVerification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ownership_verifications"

    project_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    method: Mapped[str] = mapped_column(String(40), default="repository_file", nullable=False)
    challenge_token: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=VerificationStatus.PENDING.value, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
