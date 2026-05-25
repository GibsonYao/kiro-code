"""Task service layer — business logic for task CRUD and operations."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus, TaskType


async def get_tasks(
    db: AsyncSession,
    family_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    status: TaskStatus | None = None,
    assignee_id: uuid.UUID | None = None,
) -> tuple[list[Task], int]:
    """Get paginated list of tasks for a family.

    Args:
        db: Database session.
        family_id: Family UUID to filter by.
        page: Page number (1-indexed).
        page_size: Number of items per page.
        status: Optional status filter.
        assignee_id: Optional assignee filter.

    Returns:
        Tuple of (tasks list, total count).
    """
    base_query = select(Task).where(Task.family_id == family_id)

    if status is not None:
        base_query = base_query.where(Task.status == status)
    if assignee_id is not None:
        base_query = base_query.where(Task.assignee_id == assignee_id)

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch paginated results
    offset = (page - 1) * page_size
    query = base_query.order_by(Task.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    tasks = list(result.scalars().all())

    return tasks, total


async def get_bounty_tasks(
    db: AsyncSession,
    family_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Task], int]:
    """Get paginated list of claimable bounty tasks (pending, no assignee).

    Args:
        db: Database session.
        family_id: Family UUID to filter by.
        page: Page number (1-indexed).
        page_size: Number of items per page.

    Returns:
        Tuple of (tasks list, total count).
    """
    base_query = select(Task).where(
        Task.family_id == family_id,
        Task.status == TaskStatus.pending,
        Task.assignee_id.is_(None),
    )

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch paginated results
    offset = (page - 1) * page_size
    query = base_query.order_by(Task.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    tasks = list(result.scalars().all())

    return tasks, total


async def get_task_by_id(
    db: AsyncSession,
    task_id: uuid.UUID,
    family_id: uuid.UUID,
) -> Task | None:
    """Get a single task by ID, scoped to a family.

    Args:
        db: Database session.
        task_id: Task UUID.
        family_id: Family UUID for access control.

    Returns:
        Task instance or None if not found.
    """
    query = select(Task).where(Task.id == task_id, Task.family_id == family_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_task(
    db: AsyncSession,
    family_id: uuid.UUID,
    title: str,
    task_type: TaskType,
    description: str | None = None,
    plan_step_id: uuid.UUID | None = None,
    recurrence_rule: dict | None = None,
    time_limit_hours: float | None = None,
    reward_points: int = 0,
    penalty_points: int = 0,
    assignee_id: uuid.UUID | None = None,
) -> Task:
    """Create a new task.

    Args:
        db: Database session.
        family_id: Family UUID.
        title: Task title.
        task_type: Task type (once/recurring).
        description: Task description (optional).
        plan_step_id: Associated plan step UUID (optional).
        recurrence_rule: Recurrence rule JSON (optional).
        time_limit_hours: Time limit in hours (optional).
        reward_points: Reward points.
        penalty_points: Penalty points.
        assignee_id: Assignee user UUID (optional).

    Returns:
        Created Task instance.
    """
    task = Task(
        family_id=family_id,
        title=title,
        description=description,
        plan_step_id=plan_step_id,
        task_type=task_type,
        recurrence_rule=recurrence_rule,
        time_limit_hours=time_limit_hours,
        reward_points=reward_points,
        penalty_points=penalty_points,
        assignee_id=assignee_id,
        status=TaskStatus.pending,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def update_task(
    db: AsyncSession,
    task: Task,
    title: str | None = None,
    description: str | None = None,
    task_type: TaskType | None = None,
    recurrence_rule: dict | None = None,
    time_limit_hours: float | None = None,
    reward_points: int | None = None,
    penalty_points: int | None = None,
    assignee_id: uuid.UUID | None = None,
    status: TaskStatus | None = None,
) -> Task:
    """Update an existing task.

    Args:
        db: Database session.
        task: Task instance to update.
        title: New title (optional).
        description: New description (optional).
        task_type: New task type (optional).
        recurrence_rule: New recurrence rule (optional).
        time_limit_hours: New time limit (optional).
        reward_points: New reward points (optional).
        penalty_points: New penalty points (optional).
        assignee_id: New assignee ID (optional).
        status: New status (optional).

    Returns:
        Updated Task instance.
    """
    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if task_type is not None:
        task.task_type = task_type
    if recurrence_rule is not None:
        task.recurrence_rule = recurrence_rule
    if time_limit_hours is not None:
        task.time_limit_hours = time_limit_hours
    if reward_points is not None:
        task.reward_points = reward_points
    if penalty_points is not None:
        task.penalty_points = penalty_points
    if assignee_id is not None:
        task.assignee_id = assignee_id
    if status is not None:
        task.status = status

    await db.flush()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task: Task) -> None:
    """Delete a task.

    Args:
        db: Database session.
        task: Task instance to delete.
    """
    await db.delete(task)
    await db.flush()


async def claim_task(
    db: AsyncSession,
    task_id: uuid.UUID,
    family_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Task | None:
    """Claim a bounty task using SELECT FOR UPDATE to prevent concurrent claims.

    Args:
        db: Database session.
        task_id: Task UUID to claim.
        family_id: Family UUID for access control.
        user_id: User UUID claiming the task.

    Returns:
        Claimed Task instance, or None if task not found or not claimable.
    """
    # Use SELECT FOR UPDATE to lock the row
    query = (
        select(Task)
        .where(
            Task.id == task_id,
            Task.family_id == family_id,
            Task.status == TaskStatus.pending,
            Task.assignee_id.is_(None),
        )
        .with_for_update()
    )
    result = await db.execute(query)
    task = result.scalar_one_or_none()

    if task is None:
        return None

    # Claim the task
    task.assignee_id = user_id
    task.status = TaskStatus.claimed

    # Calculate deadline if time_limit_hours is set
    if task.time_limit_hours:
        task.deadline_at = datetime.now(timezone.utc) + timedelta(hours=task.time_limit_hours)

    await db.flush()
    await db.refresh(task)
    return task


async def submit_task(
    db: AsyncSession,
    task: Task,
) -> Task:
    """Mark a task as submitted for review.

    Args:
        db: Database session.
        task: Task instance to submit.

    Returns:
        Updated Task instance with submitted status.
    """
    task.status = TaskStatus.submitted
    await db.flush()
    await db.refresh(task)
    return task
