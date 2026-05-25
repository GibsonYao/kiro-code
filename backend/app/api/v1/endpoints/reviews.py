"""Reviews API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_family, get_current_user, get_db
from app.models.family import FamilyMember
from app.models.review import ReviewStatus
from app.models.user import User
from app.schemas.review import (
    ReviewApproveRequest,
    ReviewListResponse,
    ReviewRejectRequest,
    ReviewResponse,
)
from app.services.review_service import (
    approve_review,
    get_pending_reviews,
    get_review_by_id,
    reject_review,
)

router = APIRouter()


@router.get("/pending", response_model=ReviewListResponse)
async def list_pending_reviews(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of pending reviews for the current user as reviewer."""
    reviews, total = await get_pending_reviews(
        db=db,
        family_id=membership.family_id,
        reviewer_id=current_user.id,
        page=page,
        page_size=page_size,
    )

    return ReviewListResponse(
        items=[ReviewResponse.model_validate(r) for r in reviews],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.post("/{review_id}/approve", response_model=ReviewResponse)
async def approve_review_endpoint(
    review_id: uuid.UUID,
    body: ReviewApproveRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Approve a review. Only the assigned reviewer can approve."""
    review = await get_review_by_id(db=db, review_id=review_id, family_id=membership.family_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="审核记录不存在",
        )

    # Only the assigned reviewer can approve
    if review.reviewer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有指定的审核人可以审批",
        )

    # Can only approve pending reviews
    if review.status != ReviewStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能审批待审核的记录",
        )

    review = await approve_review(db=db, review=review, comment=body.comment)
    return ReviewResponse.model_validate(review)


@router.post("/{review_id}/reject", response_model=ReviewResponse)
async def reject_review_endpoint(
    review_id: uuid.UUID,
    body: ReviewRejectRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Reject a review. Only the assigned reviewer can reject."""
    review = await get_review_by_id(db=db, review_id=review_id, family_id=membership.family_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="审核记录不存在",
        )

    # Only the assigned reviewer can reject
    if review.reviewer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有指定的审核人可以驳回",
        )

    # Can only reject pending reviews
    if review.status != ReviewStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能驳回待审核的记录",
        )

    review = await reject_review(db=db, review=review, comment=body.comment)
    return ReviewResponse.model_validate(review)
