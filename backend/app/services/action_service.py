"""Action service layer — business logic for action CRUD and operations."""

import uuid
from datetime import date, time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import Action, ActionStatus, ActionType
from app.models.task import Task, TaskStatus


async def get_actions(
    db: AsyncSession,
    family_id: uuid.UUID,
    user_id: uuid.UUID | None = None,
    action_type: ActionType | None = None,
    status: ActionStatus | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Action], int]:
    """Get paginated list of actions for a family.

    Args:
        db: Database session.
        family_id: Family UUID to filter by.
        user_id: Optional user filter.
        action_type: Optional action type filter (todo/schedule).
        status: Optional status filter.
        page: Page number (1-indexed).
        page_size: Number of items per page.

    Returns:
        Tuple of (actions list, total count).
    """
    base_query = select(Action).where(Action.family_id == family_id)

    if user_id is not None:
        base_query = base_query.where(Action.user_id == user_id)
    if action_type is not None:
        base_query = base_query.where(Action.action_type == action_type)
    if status is not None:
        base_query = base_query.where(Action.status == status)

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch paginated results
    offset = (page - 1) * page_size
    query = base_query.order_by(Action.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    actions = list(result.scalars().all())

    return actions, total


async def get_action_by_id(
    db: AsyncSession,
    action_id: uuid.UUID,
    family_id: uuid.UUID,
) -> Action | None:
    """Get a single action by ID, scoped to a family.

    Args:
        db: Database session.
        action_id: Action UUID.
        family_id: Family UUID for access control.

    Returns:
        Action instance or None if not found.
    """
    query = select(Action).where(Action.id == action_id, Action.family_id == family_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_action(
    db: AsyncSession,
    family_id: uuid.UUID,
    user_id: uuid.UUID,
    title: str,
    action_type: ActionType,
    task_id: uuid.UUID | None = None,
    plan_step_id: uuid.UUID | None = None,
    scheduled_date: date | None = None,
    scheduled_time: time | None = None,
    reward_points: int = 0,
) -> Action:
    """Create a new action.

    Args:
        db: Database session.
        family_id: Family UUID.
        user_id: User UUID (action owner).
        title: Action title.
        action_type: Action type (todo/schedule).
        task_id: Associated task UUID (optional).
        plan_step_id: Associated plan step UUID (optional).
        scheduled_date: Scheduled date (optional).
        scheduled_time: Scheduled time (optional).
        reward_points: Reward points.

    Returns:
        Created Action instance.
    """
    action = Action(
        family_id=family_id,
        user_id=user_id,
        title=title,
        action_type=action_type,
        task_id=task_id,
        plan_step_id=plan_step_id,
        scheduled_date=scheduled_date,
        scheduled_time=scheduled_time,
        reward_points=reward_points,
        status=ActionStatus.pending,
    )
    db.add(action)
    await db.flush()
    await db.refresh(action)
    return action


async def update_action(
    db: AsyncSession,
    action: Action,
    title: str | None = None,
    action_type: ActionType | None = None,
    scheduled_date: date | None = None,
    scheduled_time: time | None = None,
    reward_points: int | None = None,
    status: ActionStatus | None = None,
) -> Action:
    """Update an existing action.

    Args:
        db: Database session.
        action: Action instance to update.
        title: New title (optional).
        action_type: New action type (optional).
        scheduled_date: New scheduled date (optional).
        scheduled_time: New scheduled time (optional).
        reward_points: New reward points (optional).
        status: New status (optional).

    Returns:
        Updated Action instance.
    """
    if title is not None:
        action.title = title
    if action_type is not None:
        action.action_type = action_type
    if scheduled_date is not None:
        action.scheduled_date = scheduled_date
    if scheduled_time is not None:
        action.scheduled_time = scheduled_time
    if reward_points is not None:
        action.reward_points = reward_points
    if status is not None:
        action.status = status

    await db.flush()
    await db.refresh(action)
    return action


async def delete_action(db: AsyncSession, action: Action) -> None:
    """Delete an action.

    Args:
        db: Database session.
        action: Action instance to delete.
    """
    await db.delete(action)
    await db.flush()


async def complete_action(
    db: AsyncSession,
    action: Action,
) -> Action:
    """Mark an action as submitted (completed, pending review).

    Args:
        db: Database session.
        action: Action instance to complete.

    Returns:
        Updated Action instance.
    """
    action.status = ActionStatus.submitted
    await db.flush()
    await db.refresh(action)
    return action


async def update_time_log(
    db: AsyncSession,
    action: Action,
    time_spent_minutes: int,
) -> Action:
    """Update the time spent on an action.

    Args:
        db: Database session.
        action: Action instance.
        time_spent_minutes: Time spent in minutes.

    Returns:
        Updated Action instance.
    """
    action.time_spent_minutes = time_spent_minutes
    await db.flush()
    await db.refresh(action)
    return action


async def update_task_progress_on_action_complete(
    db: AsyncSession,
    action: Action,
) -> None:
    """Update the linked task's progress when an action is completed.

    When an action linked to a task is completed, calculate the progress
    based on how many actions linked to that task are completed vs total.

    Args:
        db: Database session.
        action: The completed action.
    """
    if action.task_id is None:
        return

    # Get the linked task
    task_query = select(Task).where(Task.id == action.task_id)
    task_result = await db.execute(task_query)
    task = task_result.scalar_one_or_none()

    if task is None:
        return

    # Count total actions linked to this task
    total_query = select(func.count()).where(Action.task_id == action.task_id)
    total_result = await db.execute(total_query)
    total_actions = total_result.scalar() or 0

    # Count completed actions (submitted/approved)
    completed_query = select(func.count()).where(
        Action.task_id == action.task_id,
        Action.status.in_([ActionStatus.submitted, ActionStatus.approved]),
    )
    completed_result = await db.execute(completed_query)
    completed_actions = completed_result.scalar() or 0

    # If all actions are completed, mark task as in_progress (ready for submission)
    if total_actions > 0 and completed_actions >= total_actions:
        # Only update if task is in a state that allows progression
        if task.status in (TaskStatus.pending, TaskStatus.claimed, TaskStatus.in_progress):
            task.status = TaskStatus.in_progress
            await db.flush()
