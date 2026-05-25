"""Family, FamilyMember, and FamilyAppellation models."""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin, UUIDType


class FamilyRole(str, enum.Enum):
    """Role of a member within a family."""

    admin = "admin"
    member = "member"


class Family(UUIDMixin, TimestampMixin, Base):
    """Family group model."""

    __tablename__ = "families"

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    invite_code: Mapped[str] = mapped_column(
        String(32), unique=True, index=True, nullable=False
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )


class FamilyMember(UUIDMixin, TimestampMixin, Base):
    """Association between a user and a family."""

    __tablename__ = "family_members"
    __table_args__ = (
        UniqueConstraint("family_id", "user_id", name="uq_family_members_family_user"),
    )

    family_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("families.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )
    role: Mapped[FamilyRole] = mapped_column(
        Enum(FamilyRole, name="family_role"),
        default=FamilyRole.member,
        nullable=False,
    )
    nickname_in_family: Mapped[str | None] = mapped_column(String(64), nullable=True)
    relationship: Mapped[str | None] = mapped_column(String(64), nullable=True)


class FamilyAppellation(UUIDMixin, TimestampMixin, Base):
    """Appellation (称谓) between two family members."""

    __tablename__ = "family_appellations"
    __table_args__ = (
        UniqueConstraint(
            "family_id",
            "from_member_id",
            "to_member_id",
            name="uq_family_appellations_from_to",
        ),
    )

    family_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("families.id"), nullable=False
    )
    from_member_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("family_members.id"), nullable=False
    )
    to_member_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("family_members.id"), nullable=False
    )
    appellation: Mapped[str] = mapped_column(String(64), nullable=False)
