"""Wish service layer — business logic for wish CRUD operations."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wish import Wish, WishStatus


async def get_wishes(
    db: AsyncSession,
    family_id: uuid.UUID,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    status: WishStatus | None = None,
) -> tuple[list[Wish], int]:
    """Get paginated list of wishes for a user in a family.

    Args:
        db: Database session.
        family_id: Family UUID to filter by.
        user_id: User UUID to filter by.
        page: Page number (1-indexed).
        page_size: Number of items per page.
        status: Optional status filter.

    Returns:
        Tuple of (wishes list, total count).
    """
    base_query = select(Wish).where(
        Wish.family_id == family_id,
        Wish.user_id == user_id,
    )

    if status is not None:
        base_query = base_query.where(Wish.status == status)

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch paginated results
    offset = (page - 1) * page_size
    query = base_query.order_by(Wish.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    wishes = list(result.scalars().all())

    return wishes, total


async def get_wish_by_id(
    db: AsyncSession,
    wish_id: uuid.UUID,
    family_id: uuid.UUID,
) -> Wish | None:
    """Get a single wish by ID, scoped to a family.

    Args:
        db: Database session.
        wish_id: Wish UUID.
        family_id: Family UUID for access control.

    Returns:
        Wish instance or None if not found.
    """
    query = select(Wish).where(Wish.id == wish_id, Wish.family_id == family_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_wish(
    db: AsyncSession,
    family_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str,
) -> Wish:
    """Create a new wish.

    Args:
        db: Database session.
        family_id: Family UUID.
        user_id: User UUID (creator).
        title: Wish title.

    Returns:
        Created Wish instance.
    """
    wish = Wish(
        family_id=family_id,
        user_id=user_id,
        title=title,
        status=WishStatus.active,
    )
    db.add(wish)
    await db.flush()
    await db.refresh(wish)
    return wish


async def update_wish(
    db: AsyncSession,
    wish: Wish,
    title: str | None = None,
    status: WishStatus | None = None,
) -> Wish:
    """Update an existing wish.

    Args:
        db: Database session.
        wish: Wish instance to update.
        title: New title (optional).
        status: New status (optional).

    Returns:
        Updated Wish instance.
    """
    if title is not None:
        wish.title = title
    if status is not None:
        wish.status = status

    await db.flush()
    await db.refresh(wish)
    return wish


async def delete_wish(db: AsyncSession, wish: Wish) -> None:
    """Delete a wish.

    Args:
        db: Database session.
        wish: Wish instance to delete.
    """
    await db.delete(wish)
    await db.flush()
