"""Wishes API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_family, get_current_user, get_db
from app.models.family import FamilyMember
from app.models.user import User
from app.models.wish import WishStatus
from app.schemas.wish import (
    WishCreateRequest,
    WishListResponse,
    WishResponse,
    WishUpdateRequest,
)
from app.services.wish_service import (
    create_wish,
    delete_wish,
    get_wish_by_id,
    get_wishes,
    update_wish,
)
from app.tasks.ai_tasks import generate_vision_story

router = APIRouter()


@router.get("", response_model=WishListResponse)
async def list_wishes(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: WishStatus | None = Query(None, alias="status", description="状态筛选"),
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of wishes for the current user in their family."""
    wishes, total = await get_wishes(
        db=db,
        family_id=membership.family_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status_filter,
    )

    return WishListResponse(
        items=[WishResponse.model_validate(w) for w in wishes],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.post("", response_model=WishResponse, status_code=status.HTTP_201_CREATED)
async def create_wish_endpoint(
    body: WishCreateRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Create a new wish and trigger AI vision generation."""
    wish = await create_wish(
        db=db,
        family_id=membership.family_id,
        user_id=current_user.id,
        title=body.title,
    )

    # Trigger async AI generation task
    generate_vision_story.delay(str(wish.id))

    return WishResponse.model_validate(wish)


@router.get("/{wish_id}", response_model=WishResponse)
async def get_wish(
    wish_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get a single wish by ID."""
    wish = await get_wish_by_id(db=db, wish_id=wish_id, family_id=membership.family_id)
    if wish is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="愿望不存在",
        )
    return WishResponse.model_validate(wish)


@router.put("/{wish_id}", response_model=WishResponse)
async def update_wish_endpoint(
    wish_id: uuid.UUID,
    body: WishUpdateRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Update a wish. If title changes, triggers AI regeneration."""
    wish = await get_wish_by_id(db=db, wish_id=wish_id, family_id=membership.family_id)
    if wish is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="愿望不存在",
        )

    # Only the creator can update
    if wish.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有创建者可以编辑愿望",
        )

    title_changed = body.title is not None and body.title != wish.title

    wish = await update_wish(
        db=db,
        wish=wish,
        title=body.title,
        status=body.status,
    )

    # If title changed, regenerate AI content
    if title_changed:
        generate_vision_story.delay(str(wish.id))

    return WishResponse.model_validate(wish)


@router.delete("/{wish_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wish_endpoint(
    wish_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Delete a wish. Only the creator can delete."""
    wish = await get_wish_by_id(db=db, wish_id=wish_id, family_id=membership.family_id)
    if wish is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="愿望不存在",
        )

    if wish.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有创建者可以删除愿望",
        )

    await delete_wish(db=db, wish=wish)


@router.post("/{wish_id}/regenerate", response_model=WishResponse)
async def regenerate_wish_vision(
    wish_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Regenerate AI vision story and image for a wish."""
    wish = await get_wish_by_id(db=db, wish_id=wish_id, family_id=membership.family_id)
    if wish is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="愿望不存在",
        )

    if wish.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有创建者可以重新生成愿景",
        )

    # Trigger async AI regeneration
    generate_vision_story.delay(str(wish.id))

    return WishResponse.model_validate(wish)
