"""Country reference data."""

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Country(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "countries"

    code: Mapped[str] = mapped_column(String(2), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(120), nullable=False)
    region: Mapped[str] = mapped_column(String(60), nullable=False, default="Africa")
    flag_emoji: Mapped[str | None] = mapped_column(String(16))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    activity_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
