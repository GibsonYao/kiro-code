"""Permission checking utilities for data access control."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.family import FamilyMember, FamilyRole


async def check_delete_permission(
    db: AsyncSession,
    current_user_id: uuid.UUID,
    family_id: uuid.UUID,
    item_created_by: uuid.UUID,
) -> None:
    """Check if the current user can delete an item.

    Only the item creator or a family admin can delete items.

    Args:
        db: Database session
        current_user_id: The current authenticated user's ID
        family_id: The family context ID
        item_created_by: The user ID who created the item

    Raises:
        HTTPException 403 if user lacks permission to delete.
    """
    # Creator can always delete their own items
    if current_user_id == item_created_by:
        return

    # Check if user is family admin
    from sqlalchemy import select

    stmt = (
        select(FamilyMember)
        .where(FamilyMember.user_id == current_user_id)
        .where(FamilyMember.family_id == family_id)
    )
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()

    if membership is None or membership.role != FamilyRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅创建者或家庭管理员可删除此条目",
        )


def verify_family_access(
    item_family_id: uuid.UUID,
    current_family_id: uuid.UUID,
) -> None:
    """Verify that an item belongs to the current user's family.

    Args:
        item_family_id: The family_id on the data item
        current_family_id: The current user's active family_id

    Raises:
        HTTPException 403 if family IDs don't match.
    """
    if item_family_id != current_family_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问其他家庭的数据",
        )
