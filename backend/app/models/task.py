"""Task model."""

import enum
import uuid

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin, UUIDType

# Use sqlalchemy.JSON for JSON fields
from sqlalchemy import JSON


class TaskType(str, enum.Enum):
    """Type of a task."""

    once = "once"
    recurring = "recurring"


class TaskStatus(str, enum.Enum):
    """Status of a task."""

    pending = "pending"
    claimed = "claimed"
    in_progress = "in_progress"
    submitted = "submitted"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"


class Task(UUIDMixin, TimestampMixin, Base):
    """Task (任务) model — concrete execution units with rewards/penalties."""

    __tablename__ = "tasks"

    family_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("families.id"), index=True, nullable=False
    )
    plan_step_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("plan_steps.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    display_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_type: Mapped[TaskType] = mapped_column(
        Enum(TaskType, name="task_type"), nullable=False
    )
    recurrence_rule: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    time_limit_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    reward_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    penalty_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=True
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status"),
        default=TaskStatus.pending,
        nullable=False,
    )
    deadline_at: Mapped[None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
