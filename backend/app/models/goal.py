"""Goal model."""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin, UUIDType


class GoalStatus(str, enum.Enum):
    """Status of a goal."""

    active = "active"
    completed = "completed"
    archived = "archived"


class Goal(UUIDMixin, TimestampMixin, Base):
    """Goal (目标) model — SMART goals derived from wishes."""

    __tablename__ = "goals"

    family_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("families.id"), index=True, nullable=False
    )
    wish_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("wishes.id"), nullable=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    smart_specific: Mapped[str | None] = mapped_column(Text, nullable=True)
    smart_measurable: Mapped[str | None] = mapped_column(Text, nullable=True)
    smart_achievable: Mapped[str | None] = mapped_column(Text, nullable=True)
    smart_relevant: Mapped[str | None] = mapped_column(Text, nullable=True)
    smart_time_bound: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    display_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[GoalStatus] = mapped_column(
        Enum(GoalStatus, name="goal_status"),
        default=GoalStatus.active,
        nullable=False,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )
