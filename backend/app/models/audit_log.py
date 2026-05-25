"""Audit log model for tracking admin operations."""

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin, _get_uuid_type

import uuid
from datetime import datetime


class AuditLog(UUIDMixin, Base):
    """Audit log for tracking configuration changes."""

    __tablename__ = "audit_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(_get_uuid_type(), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)  # create, update, delete, activate, test
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)  # ai_config
    resource_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
