"""Review-related Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.review import ReviewStatus, ReviewTargetType


# ─── Request Schemas ───────────────────────────────────────────────────────────


class ReviewApproveRequest(BaseModel):
    """Request body for approving a review."""

    comment: str | None = Field(None, max_length=512, description="审核备注")


class ReviewRejectRequest(BaseModel):
    """Request body for rejecting a review."""

    comment: str | None = Field(None, max_length=512, description="驳回原因")


# ─── Response Schemas ──────────────────────────────────────────────────────────


class ReviewResponse(BaseModel):
    """Response containing review information."""

    id: uuid.UUID
    family_id: uuid.UUID
    target_type: ReviewTargetType
    target_id: uuid.UUID
    reviewer_id: uuid.UUID
    submitter_id: uuid.UUID
    status: ReviewStatus
    comment: str | None = None
    evidence_text: str | None = None
    evidence_photos: list | None = None
    evidence_qrcode: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    """Paginated list of reviews."""

    items: list[ReviewResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
