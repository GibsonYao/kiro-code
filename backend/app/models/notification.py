"""Notification model for in-app notifications."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin, _get_uuid_type


class NotificationType(str, enum.Enum):
    """Notification type categories."""
    task_remind = "task_remind"
    review = "review"
    points = "points"
    anniversary = "anniversary"
    system = "system"


class Notification(Base, UUIDMixin, TimestampMixin):
    """In-app notification record."""

    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        _get_uuid_type(), ForeignKey("users.id"), nullable=False, index=True
    )
    family_id: Mapped[uuid.UUID] = mapped_column(
        _get_uuid_type(), ForeignKey("families.id"), nullable=False, index=True
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType), nullable=False, default=NotificationType.system
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
