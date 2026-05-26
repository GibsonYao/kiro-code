"""Notification schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.notification import NotificationType


class NotificationOut(BaseModel):
    """Notification response schema."""
    id: UUID
    type: NotificationType
    title: str
    content: str
    is_read: bool
    target_type: str | None = None
    target_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationListOut(BaseModel):
    """Notification list response with unread count."""
    items: list[NotificationOut]
    unread_count: int


class UnreadCountOut(BaseModel):
    """Unread count response."""
    unread_count: int


class NotificationCreate(BaseModel):
    """Schema for creating a notification internally."""
    user_id: UUID
    family_id: UUID
    type: NotificationType = NotificationType.system
    title: str
    content: str = ""
    target_type: str | None = None
    target_id: str | None = None
