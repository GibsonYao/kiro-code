"""SQLAlchemy base model and common mixins."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, TypeDecorator, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import settings


def _is_sqlite() -> bool:
    """Check if we're using SQLite backend."""
    return settings.DATABASE_URL.startswith("sqlite")


class SQLiteUUID(TypeDecorator):
    """Platform-independent UUID type.
    
    Uses String(32) on SQLite, native UUID on PostgreSQL.
    Automatically converts between Python uuid.UUID objects and hex strings.
    """
    impl = String(32)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value.hex
        # Already a string, strip dashes
        return str(value).replace('-', '')

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


def _get_uuid_type():
    """Return the appropriate UUID column type based on database backend."""
    if _is_sqlite():
        return SQLiteUUID()
    else:
        from sqlalchemy.dialects.postgresql import UUID
        return UUID(as_uuid=True)


# Shared UUID column type - use this for ALL uuid columns
UUIDType = _get_uuid_type()


def _uuid_default():
    """Generate a UUID value."""
    return uuid.uuid4()


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class UUIDMixin:
    """Mixin that provides a UUID primary key field."""

    id: Mapped[uuid.UUID] = mapped_column(
        _get_uuid_type(),
        primary_key=True,
        default=_uuid_default,
    )


class TimestampMixin:
    """Mixin that provides created_at and updated_at fields."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
