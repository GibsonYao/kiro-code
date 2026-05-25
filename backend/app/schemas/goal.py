"""Goal-related Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.goal import GoalStatus


# ─── Request Schemas ───────────────────────────────────────────────────────────


class GoalCreateRequest(BaseModel):
    """Request body for creating a goal."""

    title: str = Field(..., min_length=1, max_length=256, description="目标标题")
    description: str | None = Field(None, max_length=2000, description="目标描述")
    wish_id: uuid.UUID | None = Field(None, description="关联愿望ID（可空）")


class GoalUpdateRequest(BaseModel):
    """Request body for updating a goal."""

    title: str | None = Field(None, min_length=1, max_length=256, description="目标标题")
    description: str | None = Field(None, max_length=2000, description="目标描述")
    status: GoalStatus | None = Field(None, description="目标状态")
    progress: int | None = Field(None, ge=0, le=100, description="进度(0-100)")


# ─── Response Schemas ──────────────────────────────────────────────────────────


class GoalResponse(BaseModel):
    """Response containing goal information."""

    id: uuid.UUID
    family_id: uuid.UUID
    wish_id: uuid.UUID | None = None
    user_id: uuid.UUID
    title: str
    description: str | None = None
    smart_specific: str | None = None
    smart_measurable: str | None = None
    smart_achievable: str | None = None
    smart_relevant: str | None = None
    smart_time_bound: str | None = None
    cover_image_url: str | None = None
    display_text: str | None = None
    progress: int
    status: GoalStatus
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GoalListResponse(BaseModel):
    """Paginated list of goals."""

    items: list[GoalResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# ─── Chain Response Schemas ────────────────────────────────────────────────────


class ChainWishItem(BaseModel):
    """Wish item in chain view."""

    id: uuid.UUID
    title: str
    vision_story: str | None = None
    vision_image_url: str | None = None
    cover_image_url: str | None = None
    display_text: str | None = None
    status: str

    model_config = {"from_attributes": True}


class ChainActionItem(BaseModel):
    """Action item in chain view."""

    id: uuid.UUID
    title: str
    cover_image_url: str | None = None
    display_text: str | None = None
    action_type: str
    status: str

    model_config = {"from_attributes": True}


class ChainTaskItem(BaseModel):
    """Task item in chain view."""

    id: uuid.UUID
    title: str
    cover_image_url: str | None = None
    display_text: str | None = None
    task_type: str
    status: str
    reward_points: int
    penalty_points: int
    actions: list[ChainActionItem] = []

    model_config = {"from_attributes": True}


class ChainPlanStepItem(BaseModel):
    """Plan step item in chain view."""

    id: uuid.UUID
    title: str
    step_type: str
    is_bounty: bool
    status: str

    model_config = {"from_attributes": True}


class ChainPlanItem(BaseModel):
    """Plan item in chain view."""

    id: uuid.UUID
    title: str
    cover_image_url: str | None = None
    display_text: str | None = None
    status: str
    start_date: str | None = None
    end_date: str | None = None
    steps: list[ChainPlanStepItem] = []
    tasks: list[ChainTaskItem] = []

    model_config = {"from_attributes": True}


class GoalChainResponse(BaseModel):
    """Full chain response: wish → goal → plans → tasks → actions."""

    wish: ChainWishItem | None = None
    goal: GoalResponse
    plans: list[ChainPlanItem] = []
