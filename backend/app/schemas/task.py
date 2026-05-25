"""Task-related Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.task import TaskStatus, TaskType


# ─── Request Schemas ───────────────────────────────────────────────────────────


class TaskCreateRequest(BaseModel):
    """Request body for creating a task."""

    title: str = Field(..., min_length=1, max_length=256, description="任务标题")
    description: str | None = Field(None, description="任务描述")
    plan_step_id: uuid.UUID | None = Field(None, description="关联计划步骤ID（可空）")
    task_type: TaskType = Field(..., description="任务类型（once/recurring）")
    recurrence_rule: dict | None = Field(None, description="重复规则（JSON）")
    time_limit_hours: float | None = Field(None, ge=0, description="时限（小时）")
    reward_points: int = Field(0, ge=0, description="奖励积分")
    penalty_points: int = Field(0, ge=0, description="惩罚积分")
    assignee_id: uuid.UUID | None = Field(None, description="指派人ID（可空）")


class TaskUpdateRequest(BaseModel):
    """Request body for updating a task."""

    title: str | None = Field(None, min_length=1, max_length=256, description="任务标题")
    description: str | None = Field(None, description="任务描述")
    task_type: TaskType | None = Field(None, description="任务类型")
    recurrence_rule: dict | None = Field(None, description="重复规则")
    time_limit_hours: float | None = Field(None, ge=0, description="时限（小时）")
    reward_points: int | None = Field(None, ge=0, description="奖励积分")
    penalty_points: int | None = Field(None, ge=0, description="惩罚积分")
    assignee_id: uuid.UUID | None = Field(None, description="指派人ID")
    status: TaskStatus | None = Field(None, description="任务状态")


class TaskSubmitRequest(BaseModel):
    """Request body for submitting a task completion."""

    evidence_text: str | None = Field(None, description="文字描述验证")
    evidence_photos: list[str] | None = Field(None, description="照片URL列表")
    evidence_qrcode: str | None = Field(None, description="扫码验证内容")


# ─── Response Schemas ──────────────────────────────────────────────────────────


class TaskResponse(BaseModel):
    """Response containing task information."""

    id: uuid.UUID
    family_id: uuid.UUID
    plan_step_id: uuid.UUID | None = None
    title: str
    description: str | None = None
    cover_image_url: str | None = None
    display_text: str | None = None
    task_type: TaskType
    recurrence_rule: dict | None = None
    time_limit_hours: float | None = None
    reward_points: int
    penalty_points: int
    assignee_id: uuid.UUID | None = None
    status: TaskStatus
    deadline_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    """Paginated list of tasks."""

    items: list[TaskResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
