"""AIModelConfig model."""

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin

# Use sqlalchemy.JSON for JSON fields
from sqlalchemy import JSON


class AIModelConfig(UUIDMixin, TimestampMixin, Base):
    """AI model configuration for dynamic provider management."""

    __tablename__ = "ai_model_configs"

    config_key: Mapped[str] = mapped_column(String(64), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    api_key: Mapped[str] = mapped_column(String(512), nullable=False)
    api_base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    parameters: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
