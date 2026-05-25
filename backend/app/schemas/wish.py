"""Wish-related Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.wish import WishStatus


# ─── Request Schemas ───────────────────────────────────────────────────────────


class WishCreateRequest(BaseModel):
    """Request body for creating a wish."""

    title: str = Field(..., min_length=1, max_length=256, description="愿望标题")


class WishUpdateRequest(BaseModel):
    """Request body for updating a wish."""

    title: str | None = Field(None, min_length=1, max_length=256, description="愿望标题")
    status: WishStatus | None = Field(None, description="愿望状态")


# ─── Response Schemas ──────────────────────────────────────────────────────────


class WishResponse(BaseModel):
    """Response containing wish information."""

    id: uuid.UUID
    family_id: uuid.UUID
    user_id: uuid.UUID
    title: str
    vision_story: str | None = None
    vision_image_url: str | None = None
    cover_image_url: str | None = None
    display_text: str | None = None
    status: WishStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WishListResponse(BaseModel):
    """Paginated list of wishes."""

    items: list[WishResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
