"""Tests for models/base.py - Base model and mixins."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, inspect
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base, TimestampMixin, UUIDMixin


def test_base_is_declarative_base():
    """Base should be a valid DeclarativeBase subclass."""
    assert hasattr(Base, "metadata")
    assert hasattr(Base, "registry")


def test_uuid_mixin_has_id_field():
    """UUIDMixin should define an id column as UUID primary key."""
    assert hasattr(UUIDMixin, "id")
    # Check the mapped_column properties via __table__ on a concrete model
    from sqlalchemy.orm import Mapped, mapped_column

    # Verify the annotation type
    annotations = UUIDMixin.__annotations__
    assert "id" in annotations


def test_timestamp_mixin_has_timestamp_fields():
    """TimestampMixin should define created_at and updated_at columns."""
    assert hasattr(TimestampMixin, "created_at")
    assert hasattr(TimestampMixin, "updated_at")
    annotations = TimestampMixin.__annotations__
    assert "created_at" in annotations
    assert "updated_at" in annotations


def test_concrete_model_with_mixins():
    """A concrete model using both mixins should have all expected columns."""

    class TestModel(UUIDMixin, TimestampMixin, Base):
        __tablename__ = "test_model_mixin_check"

    # Inspect the table columns
    table = TestModel.__table__
    column_names = {col.name for col in table.columns}
    assert "id" in column_names
    assert "created_at" in column_names
    assert "updated_at" in column_names

    # Check id is primary key and UUID type
    id_col = table.c.id
    assert id_col.primary_key
    assert isinstance(id_col.type, UUID)

    # Check timestamps are timezone-aware
    created_col = table.c.created_at
    assert isinstance(created_col.type, DateTime)
    assert created_col.type.timezone is True

    updated_col = table.c.updated_at
    assert isinstance(updated_col.type, DateTime)
    assert updated_col.type.timezone is True

    # Check that id has a default
    assert id_col.default is not None
