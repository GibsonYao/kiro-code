"""Action-related Pydantic schemas."""

import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, Field

from app.models.action import ActionStatus, ActionType


# ─── Request Schemas ───────────────────────────────────────────────────────────


class ActionCreateRequest(BaseModel):
    """Request body for creating an action."""

    title: str = Field(..., min_length=1, max_length=256, description="行动标题")
    action_type: ActionType = Field(..., description="行动类型（todo/schedule）")
    task_id: uuid.UUID | None = Field(None, description="关联任务ID（可空）")
    plan_step_id: uuid.UUID | None = Field(None, description="关联计划步骤ID（可空）")
    scheduled_date: date | None = Field(None, description="计划日期（日程类型）")
    scheduled_time: time | None = Field(None, description="计划时间（日程类型）")
    reward_points: int = Field(0, ge=0, description="奖励积分")


class ActionUpdateRequest(BaseModel):
    """Request body for updating an action."""

    title: str | None = Field(None, min_length=1, max_length=256, description="行动标题")
    action_type: ActionType | None = Field(None, description="行动类型")
    scheduled_date: date | None = Field(None, description="计划日期")
    scheduled_time: time | None = Field(None, description="计划时间")
    reward_points: int | None = Field(None, ge=0, description="奖励积分")
    status: ActionStatus | None = Field(None, description="行动状态")


class ActionTimeLogRequest(BaseModel):
    """Request body for recording time spent on an action."""

    time_spent_minutes: int = Field(..., ge=0, description="花费时间（分钟）")


# ─── Response Schemas ──────────────────────────────────────────────────────────


class ActionResponse(BaseModel):
    """Response containing action information."""

    id: uuid.UUID
    family_id: uuid.UUID
    task_id: uuid.UUID | None = None
    plan_step_id: uuid.UUID | None = None
    user_id: uuid.UUID
    title: str
    cover_image_url: str | None = None
    display_text: str | None = None
    action_type: ActionType
    scheduled_date: date | None = None
    scheduled_time: time | None = None
    time_spent_minutes: int | None = None
    reward_points: int
    status: ActionStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ActionListResponse(BaseModel):
    """Paginated list of actions."""

    items: list[ActionResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
