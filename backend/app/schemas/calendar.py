"""Calendar event-related Pydantic schemas."""

import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, Field

from app.models.calendar import CalendarEventType


# ─── Request Schemas ───────────────────────────────────────────────────────────


class CalendarEventCreateRequest(BaseModel):
    """Request body for creating a calendar event."""

    title: str = Field(..., min_length=1, max_length=256, description="事件标题")
    event_type: CalendarEventType = Field(..., description="事件类型（schedule/todo/anniversary）")
    event_date: date | None = Field(None, description="事件日期")
    event_time: time | None = Field(None, description="事件时间")
    is_recurring: bool = Field(False, description="是否重复")
    remind_before_days: int = Field(0, ge=0, description="提前提醒天数")


class CalendarEventUpdateRequest(BaseModel):
    """Request body for updating a calendar event."""

    title: str | None = Field(None, min_length=1, max_length=256, description="事件标题")
    event_type: CalendarEventType | None = Field(None, description="事件类型")
    event_date: date | None = Field(None, description="事件日期")
    event_time: time | None = Field(None, description="事件时间")
    is_recurring: bool | None = Field(None, description="是否重复")
    remind_before_days: int | None = Field(None, ge=0, description="提前提醒天数")


# ─── Response Schemas ──────────────────────────────────────────────────────────


class CalendarEventResponse(BaseModel):
    """Response containing calendar event information."""

    id: uuid.UUID
    family_id: uuid.UUID
    user_id: uuid.UUID
    title: str
    cover_image_url: str | None = None
    event_type: CalendarEventType
    event_date: date | None = None
    event_time: time | None = None
    is_recurring: bool
    remind_before_days: int
    action_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CalendarEventListResponse(BaseModel):
    """Paginated list of calendar events."""

    items: list[CalendarEventResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ─── Anniversary Schemas (Task 16.2) ──────────────────────────────────────────


class AnniversaryCreateRequest(BaseModel):
    """Request body for creating a family anniversary."""

    title: str = Field(..., min_length=1, max_length=256, description="纪念日标题（如：爸爸生日、结婚纪念日）")
    event_date: date = Field(..., description="纪念日日期")
    remind_before_days: int = Field(3, ge=0, description="提前提醒天数")


class AnniversaryListResponse(BaseModel):
    """Paginated list of anniversaries."""

    items: list[CalendarEventResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
