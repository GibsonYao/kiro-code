"""Action model."""

import enum
import uuid

from sqlalchemy import Date, Enum, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin, UUIDType


class ActionType(str, enum.Enum):
    """Type of an action."""

    todo = "todo"
    schedule = "schedule"


class ActionStatus(str, enum.Enum):
    """Status of an action."""

    pending = "pending"
    in_progress = "in_progress"
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"


class Action(UUIDMixin, TimestampMixin, Base):
    """Action (行动) model — smallest execution unit."""

    __tablename__ = "actions"

    family_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("families.id"), index=True, nullable=False
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("tasks.id"), nullable=True
    )
    plan_step_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("plan_steps.id"), nullable=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    cover_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    display_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_type: Mapped[ActionType] = mapped_column(
        Enum(ActionType, name="action_type"), nullable=False
    )
    scheduled_date: Mapped[None] = mapped_column(Date, nullable=True)
    scheduled_time: Mapped[None] = mapped_column(Time, nullable=True)
    time_spent_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reward_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[ActionStatus] = mapped_column(
        Enum(ActionStatus, name="action_status"),
        default=ActionStatus.pending,
        nullable=False,
    )
