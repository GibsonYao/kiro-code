"""Plan and PlanStep models."""

import enum
import uuid

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin, UUIDType


class PlanStatus(str, enum.Enum):
    """Status of a plan."""

    draft = "draft"
    active = "active"
    completed = "completed"
    overdue = "overdue"


class StepType(str, enum.Enum):
    """Type of a plan step."""

    task = "task"
    action = "action"


class PlanStepStatus(str, enum.Enum):
    """Status of a plan step."""

    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"


class Plan(UUIDMixin, TimestampMixin, Base):
    """Plan (计划) model — execution plans for goals."""

    __tablename__ = "plans"

    family_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("families.id"), index=True, nullable=False
    )
    goal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("goals.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    cover_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    display_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[None] = mapped_column(Date, nullable=True)
    end_date: Mapped[None] = mapped_column(Date, nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )
    status: Mapped[PlanStatus] = mapped_column(
        Enum(PlanStatus, name="plan_status"),
        default=PlanStatus.draft,
        nullable=False,
    )

    # Relationships
    steps: Mapped[list["PlanStep"]] = relationship(
        "PlanStep",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="PlanStep.sort_order",
    )


class PlanStep(UUIDMixin, TimestampMixin, Base):
    """PlanStep model — individual steps within a plan."""

    __tablename__ = "plan_steps"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("plans.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    step_type: Mapped[StepType] = mapped_column(
        Enum(StepType, name="step_type"), nullable=False
    )
    is_bounty: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[PlanStepStatus] = mapped_column(
        Enum(PlanStepStatus, name="plan_step_status"),
        default=PlanStepStatus.pending,
        nullable=False,
    )

    # Relationships
    plan: Mapped["Plan"] = relationship("Plan", back_populates="steps")
