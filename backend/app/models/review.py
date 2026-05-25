"""Review model."""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin, UUIDType

# Use sqlalchemy.JSON for JSON fields
from sqlalchemy import JSON


class ReviewTargetType(str, enum.Enum):
    """Type of entity being reviewed."""

    task = "task"
    action = "action"


class ReviewStatus(str, enum.Enum):
    """Status of a review."""

    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Review(UUIDMixin, TimestampMixin, Base):
    """Review (审核) model — approval workflow for tasks and actions."""

    __tablename__ = "reviews"

    family_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("families.id"), index=True, nullable=False
    )
    target_type: Mapped[ReviewTargetType] = mapped_column(
        Enum(ReviewTargetType, name="review_target_type"), nullable=False
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, nullable=False
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )
    submitter_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, name="review_status"),
        default=ReviewStatus.pending,
        nullable=False,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_photos: Mapped[list | None] = mapped_column(JSON, nullable=True)
    evidence_qrcode: Mapped[str | None] = mapped_column(String(512), nullable=True)
