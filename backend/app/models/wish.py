"""Wish model."""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin, UUIDType


class WishStatus(str, enum.Enum):
    """Status of a wish."""

    active = "active"
    achieved = "achieved"
    archived = "archived"


class Wish(UUIDMixin, TimestampMixin, Base):
    """Wish (愿望) model — the starting point of the goal management chain."""

    __tablename__ = "wishes"

    family_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("families.id"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    vision_story: Mapped[str | None] = mapped_column(Text, nullable=True)
    vision_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    display_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[WishStatus] = mapped_column(
        Enum(WishStatus, name="wish_status"),
        default=WishStatus.active,
        nullable=False,
    )
