"""Goal service layer — business logic for goal CRUD operations."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal, GoalStatus


async def get_goals(
    db: AsyncSession,
    family_id: uuid.UUID,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    status: GoalStatus | None = None,
) -> tuple[list[Goal], int]:
    """Get paginated list of goals for a user in a family.

    Args:
        db: Database session.
        family_id: Family UUID to filter by.
        user_id: User UUID to filter by.
        page: Page number (1-indexed).
        page_size: Number of items per page.
        status: Optional status filter.

    Returns:
        Tuple of (goals list, total count).
    """
    base_query = select(Goal).where(
        Goal.family_id == family_id,
        Goal.user_id == user_id,
    )

    if status is not None:
        base_query = base_query.where(Goal.status == status)

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch paginated results
    offset = (page - 1) * page_size
    query = base_query.order_by(Goal.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    goals = list(result.scalars().all())

    return goals, total


async def get_goal_by_id(
    db: AsyncSession,
    goal_id: uuid.UUID,
    family_id: uuid.UUID,
) -> Goal | None:
    """Get a single goal by ID, scoped to a family.

    Args:
        db: Database session.
        goal_id: Goal UUID.
        family_id: Family UUID for access control.

    Returns:
        Goal instance or None if not found.
    """
    query = select(Goal).where(Goal.id == goal_id, Goal.family_id == family_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_goal(
    db: AsyncSession,
    family_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str,
    description: str | None = None,
    wish_id: uuid.UUID | None = None,
) -> Goal:
    """Create a new goal.

    Args:
        db: Database session.
        family_id: Family UUID.
        user_id: User UUID (creator).
        title: Goal title.
        description: Goal description (optional).
        wish_id: Associated wish UUID (optional).

    Returns:
        Created Goal instance.
    """
    goal = Goal(
        family_id=family_id,
        user_id=user_id,
        title=title,
        description=description,
        wish_id=wish_id,
        status=GoalStatus.active,
        progress=0,
        owner_id=user_id,
    )
    db.add(goal)
    await db.flush()
    await db.refresh(goal)
    return goal


async def update_goal(
    db: AsyncSession,
    goal: Goal,
    title: str | None = None,
    description: str | None = None,
    status: GoalStatus | None = None,
    progress: int | None = None,
) -> Goal:
    """Update an existing goal.

    Args:
        db: Database session.
        goal: Goal instance to update.
        title: New title (optional).
        description: New description (optional).
        status: New status (optional).
        progress: New progress value (optional).

    Returns:
        Updated Goal instance.
    """
    if title is not None:
        goal.title = title
    if description is not None:
        goal.description = description
    if status is not None:
        goal.status = status
    if progress is not None:
        goal.progress = progress

    await db.flush()
    await db.refresh(goal)
    return goal


async def delete_goal(db: AsyncSession, goal: Goal) -> None:
    """Delete a goal.

    Args:
        db: Database session.
        goal: Goal instance to delete.
    """
    await db.delete(goal)
    await db.flush()
