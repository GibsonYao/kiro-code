"""Cascade unlink service — check downstream links and unlink them before deletion.

When deleting an upstream entity (e.g., a Wish), downstream entities (e.g., Goals)
should have their foreign key set to NULL (unlinked) rather than being cascade-deleted.
This service provides:
1. check_downstream_links: Returns counts of downstream items linked to an entity.
2. unlink_downstream: Sets downstream foreign keys to NULL.
"""

import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import Action
from app.models.goal import Goal
from app.models.plan import Plan, PlanStep
from app.models.task import Task

# Valid entity types for cascade unlink operations
VALID_ENTITY_TYPES = ("wish", "goal", "plan", "task")


async def check_downstream_links(
    db: AsyncSession,
    entity_type: str,
    entity_id: uuid.UUID,
) -> dict:
    """Check how many downstream items are linked to the given entity.

    Args:
        db: Database session.
        entity_type: Type of entity ("wish", "goal", "plan", "task").
        entity_id: UUID of the entity to check.

    Returns:
        Dictionary with counts of downstream items, e.g.:
        {"goals": 3} for a wish, {"plans": 2} for a goal, etc.

    Raises:
        ValueError: If entity_type is not valid.
    """
    if entity_type not in VALID_ENTITY_TYPES:
        raise ValueError(
            f"Invalid entity_type: {entity_type}. Must be one of {VALID_ENTITY_TYPES}"
        )

    if entity_type == "wish":
        # Count goals linked to this wish
        result = await db.execute(
            select(func.count()).select_from(Goal).where(Goal.wish_id == entity_id)
        )
        goals_count = result.scalar() or 0
        return {"goals": goals_count}

    elif entity_type == "goal":
        # Count plans linked to this goal
        result = await db.execute(
            select(func.count()).select_from(Plan).where(Plan.goal_id == entity_id)
        )
        plans_count = result.scalar() or 0
        return {"plans": plans_count}

    elif entity_type == "plan":
        # Count tasks and actions linked to this plan's steps
        # First get all plan_step IDs for this plan
        step_ids_result = await db.execute(
            select(PlanStep.id).where(PlanStep.plan_id == entity_id)
        )
        step_ids = list(step_ids_result.scalars().all())

        if not step_ids:
            return {"tasks": 0, "actions": 0}

        # Count tasks linked to these plan steps
        tasks_result = await db.execute(
            select(func.count())
            .select_from(Task)
            .where(Task.plan_step_id.in_(step_ids))
        )
        tasks_count = tasks_result.scalar() or 0

        # Count actions linked to these plan steps
        actions_result = await db.execute(
            select(func.count())
            .select_from(Action)
            .where(Action.plan_step_id.in_(step_ids))
        )
        actions_count = actions_result.scalar() or 0

        return {"tasks": tasks_count, "actions": actions_count}

    else:  # entity_type == "task"
        # Count actions linked to this task
        result = await db.execute(
            select(func.count()).select_from(Action).where(Action.task_id == entity_id)
        )
        actions_count = result.scalar() or 0
        return {"actions": actions_count}


async def unlink_downstream(
    db: AsyncSession,
    entity_type: str,
    entity_id: uuid.UUID,
) -> None:
    """Unlink downstream items by setting their foreign keys to NULL.

    Args:
        db: Database session.
        entity_type: Type of entity ("wish", "goal", "plan", "task").
        entity_id: UUID of the entity whose downstream links should be removed.

    Raises:
        ValueError: If entity_type is not valid.
    """
    if entity_type not in VALID_ENTITY_TYPES:
        raise ValueError(
            f"Invalid entity_type: {entity_type}. Must be one of {VALID_ENTITY_TYPES}"
        )

    if entity_type == "wish":
        # Set goals.wish_id = NULL where wish_id = entity_id
        await db.execute(
            update(Goal).where(Goal.wish_id == entity_id).values(wish_id=None)
        )

    elif entity_type == "goal":
        # Set plans.goal_id = NULL where goal_id = entity_id
        await db.execute(
            update(Plan).where(Plan.goal_id == entity_id).values(goal_id=None)
        )

    elif entity_type == "plan":
        # Get all plan_step IDs for this plan
        step_ids_result = await db.execute(
            select(PlanStep.id).where(PlanStep.plan_id == entity_id)
        )
        step_ids = list(step_ids_result.scalars().all())

        if step_ids:
            # Set tasks.plan_step_id = NULL for all steps in this plan
            await db.execute(
                update(Task)
                .where(Task.plan_step_id.in_(step_ids))
                .values(plan_step_id=None)
            )

            # Set actions.plan_step_id = NULL for all steps in this plan
            await db.execute(
                update(Action)
                .where(Action.plan_step_id.in_(step_ids))
                .values(plan_step_id=None)
            )

    else:  # entity_type == "task"
        # Set actions.task_id = NULL where task_id = entity_id
        await db.execute(
            update(Action).where(Action.task_id == entity_id).values(task_id=None)
        )

    await db.flush()
