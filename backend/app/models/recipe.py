"""Recipe and MemberFoodPreference models."""

import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin, UUIDType

# Use sqlalchemy.JSON for JSON fields
from sqlalchemy import JSON


class Recipe(UUIDMixin, TimestampMixin, Base):
    """Recipe (食谱) model."""

    __tablename__ = "recipes"

    family_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("families.id"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    display_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingredients: Mapped[list | None] = mapped_column(JSON, nullable=True)
    steps: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )


class MemberFoodPreference(UUIDMixin, TimestampMixin, Base):
    """Member food preference model."""

    __tablename__ = "member_food_preferences"
    __table_args__ = (
        UniqueConstraint(
            "family_id", "user_id", name="uq_member_food_preferences_family_user"
        ),
    )

    family_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("families.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )
    taste_preferences: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    favorite_foods: Mapped[list | None] = mapped_column(JSON, nullable=True)
    food_allergies: Mapped[list | None] = mapped_column(JSON, nullable=True)
    dietary_restrictions: Mapped[list | None] = mapped_column(JSON, nullable=True)
