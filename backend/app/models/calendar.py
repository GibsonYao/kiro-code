"""CalendarEvent model."""

import enum
import uuid

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin, UUIDType


class CalendarEventType(str, enum.Enum):
    """Type of calendar event."""

    schedule = "schedule"
    todo = "todo"
    anniversary = "anniversary"


class CalendarEvent(UUIDMixin, TimestampMixin, Base):
    """Calendar event model."""

    __tablename__ = "calendar_events"

    family_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("families.id"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    cover_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    event_type: Mapped[CalendarEventType] = mapped_column(
        Enum(CalendarEventType, name="calendar_event_type"), nullable=False
    )
    event_date: Mapped[None] = mapped_column(Date, nullable=True)
    event_time: Mapped[None] = mapped_column(Time, nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    remind_before_days: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    action_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("actions.id"), nullable=True
    )
