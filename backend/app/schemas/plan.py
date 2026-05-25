"""Plan-related Pydantic schemas."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.plan import PlanStatus, PlanStepStatus, StepType


# ─── Request Schemas ───────────────────────────────────────────────────────────


class PlanCreateRequest(BaseModel):
    """Request body for creating a plan."""

    title: str = Field(..., min_length=1, max_length=256, description="计划标题")
    goal_id: uuid.UUID | None = Field(None, description="关联目标ID（可空）")
    start_date: date | None = Field(None, description="开始日期")
    end_date: date | None = Field(None, description="结束日期")
    owner_id: uuid.UUID = Field(..., description="负责人用户ID")


class PlanUpdateRequest(BaseModel):
    """Request body for updating a plan."""

    title: str | None = Field(None, min_length=1, max_length=256, description="计划标题")
    start_date: date | None = Field(None, description="开始日期")
    end_date: date | None = Field(None, description="结束日期")
    owner_id: uuid.UUID | None = Field(None, description="负责人用户ID")
    status: PlanStatus | None = Field(None, description="计划状态")


class PlanStepCreateRequest(BaseModel):
    """Request body for creating a plan step."""

    title: str = Field(..., min_length=1, max_length=256, description="步骤标题")
    step_type: StepType = Field(..., description="步骤类型（task/action）")
    is_bounty: bool = Field(False, description="是否为悬赏任务")
    sort_order: int = Field(0, ge=0, description="排序序号")


class PlanStepUpdateRequest(BaseModel):
    """Request body for updating a plan step."""

    title: str | None = Field(None, min_length=1, max_length=256, description="步骤标题")
    step_type: StepType | None = Field(None, description="步骤类型（task/action）")
    is_bounty: bool | None = Field(None, description="是否为悬赏任务")
    sort_order: int | None = Field(None, ge=0, description="排序序号")
    status: PlanStepStatus | None = Field(None, description="步骤状态")


# ─── Response Schemas ──────────────────────────────────────────────────────────


class PlanStepResponse(BaseModel):
    """Response containing plan step information."""

    id: uuid.UUID
    plan_id: uuid.UUID
    title: str
    step_type: StepType
    is_bounty: bool
    sort_order: int
    status: PlanStepStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlanResponse(BaseModel):
    """Response containing plan information."""

    id: uuid.UUID
    family_id: uuid.UUID
    goal_id: uuid.UUID | None = None
    title: str
    cover_image_url: str | None = None
    display_text: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    owner_id: uuid.UUID
    status: PlanStatus
    created_at: datetime
    updated_at: datetime
    steps: list[PlanStepResponse] = []

    model_config = {"from_attributes": True}


class PlanListResponse(BaseModel):
    """Paginated list of plans."""

    items: list[PlanResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
