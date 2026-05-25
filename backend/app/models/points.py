"""PointsAccount and PointsTransaction models."""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin, UUIDType


class PointsTransactionType(str, enum.Enum):
    """Type of points transaction."""

    reward = "reward"
    penalty = "penalty"
    manual_adjust = "manual_adjust"


class PointsAccount(UUIDMixin, TimestampMixin, Base):
    """Points account for a family member."""

    __tablename__ = "points_accounts"
    __table_args__ = (
        UniqueConstraint(
            "family_id", "user_id", name="uq_points_accounts_family_user"
        ),
    )

    family_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("families.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )
    balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_earned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_spent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class PointsTransaction(UUIDMixin, TimestampMixin, Base):
    """Individual points transaction record."""

    __tablename__ = "points_transactions"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("points_accounts.id"), nullable=False
    )
    type: Mapped[PointsTransactionType] = mapped_column(
        Enum(PointsTransactionType, name="points_transaction_type"), nullable=False
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    source_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, nullable=True
    )
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
