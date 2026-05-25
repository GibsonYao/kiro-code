"""User model."""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class User(UUIDMixin, TimestampMixin, Base):
    """User account model."""

    __tablename__ = "users"

    openid: Mapped[str | None] = mapped_column(
        String(128), unique=True, index=True, nullable=True
    )
    unionid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    phone: Mapped[str | None] = mapped_column(
        String(20), unique=True, index=True, nullable=True
    )
    email: Mapped[str | None] = mapped_column(
        String(256), unique=True, index=True, nullable=True
    )
    password_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    nickname: Mapped[str | None] = mapped_column(String(64), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
