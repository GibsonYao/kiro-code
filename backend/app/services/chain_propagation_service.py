"""Chain propagation service — propagates status changes up the goal management chain.

When a task or action is approved, this service:
1. Awards points to the assignee/user
2. Updates linked plan step status
3. Checks if all plan steps are completed → marks plan as completed
4. Recalculates goal progress based on plan completion
"""

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import Action, ActionStatus
from app.models.goal import Goal, GoalStatus
from app.models.plan import Plan, PlanStatus, PlanStep, PlanStepStatus
from app.models.task import Task, TaskStatus
from app.services.points_service import award_points


async def propagate_task_approval(db: AsyncSession, task: Task) -> None:
    """Propagate effects of a task being approved.

    - Awards reward_points to the task assignee
    - Updates the linked plan step status to completed (if linked)
    - Triggers plan progress check

    Args:
        db: Database session.
        task: The approved Task instance.
    """
    # Award points to assignee if reward_points > 0
    if task.reward_points > 0 and task.assignee_id is not None:
        await award_points(
            db=db,
            family_id=task.family_id,
            user_id=task.assignee_id,
            amount=task.reward_points,
            source_type="task",
            source_id=task.id,
            description=f"任务完成奖励: {task.title}",
        )

    # Update linked plan step status if task is linked to one
    if task.plan_step_id is not None:
        step_query = select(PlanStep).where(PlanStep.id == task.plan_step_id)
        step_result = await db.execute(step_query)
        plan_step = step_result.scalar_one_or_none()

        if plan_step is not None:
            plan_step.status = PlanStepStatus.completed
            await db.flush()
            await update_plan_progress(db, plan_step)


async def propagate_action_approval(db: AsyncSession, action: Action) -> None:
    """Propagate effects of an action being approved.

    - Awards reward_points to the action user
    - Updates the linked task progress (if linked to a task)
    - Updates the linked plan step status (if linked)

    Args:
        db: Database session.
        action: The approved Action instance.
    """
    # Award points to user if reward_points > 0
    if action.reward_points > 0:
        await award_points(
            db=db,
            family_id=action.family_id,
            user_id=action.user_id,
            amount=action.reward_points,
            source_type="action",
            source_id=action.id,
            description=f"行动完成奖励: {action.title}",
        )

    # If action is linked to a task, check if all actions for that task are approved
    if action.task_id is not None:
        task_query = select(Task).where(Task.id == action.task_id)
        task_result = await db.execute(task_query)
        task = task_result.scalar_one_or_none()

        if task is not None and task.plan_step_id is not None:
            # Check if all actions for this task are approved
            all_actions_query = select(func.count()).where(
                Action.task_id == task.id
            )
            all_result = await db.execute(all_actions_query)
            total_actions = all_result.scalar() or 0

            approved_actions_query = select(func.count()).where(
                Action.task_id == task.id,
                Action.status == ActionStatus.approved,
            )
            approved_result = await db.execute(approved_actions_query)
            approved_actions = approved_result.scalar() or 0

            # If all actions are approved, update the plan step
            if total_actions > 0 and total_actions == approved_actions:
                step_query = select(PlanStep).where(PlanStep.id == task.plan_step_id)
                step_result = await db.execute(step_query)
                plan_step = step_result.scalar_one_or_none()

                if plan_step is not None:
                    plan_step.status = PlanStepStatus.completed
                    await db.flush()
                    await update_plan_progress(db, plan_step)


async def update_plan_progress(db: AsyncSession, plan_step: PlanStep) -> None:
    """Check if all steps in the plan are completed; if so, mark plan as completed.

    Then triggers goal progress recalculation if the plan is linked to a goal.

    Args:
        db: Database session.
        plan_step: The PlanStep that was just completed.
    """
    plan_query = select(Plan).where(Plan.id == plan_step.plan_id)
    plan_result = await db.execute(plan_query)
    plan = plan_result.scalar_one_or_none()

    if plan is None:
        return

    # Count total and completed steps
    total_query = select(func.count()).where(PlanStep.plan_id == plan.id)
    total_result = await db.execute(total_query)
    total_steps = total_result.scalar() or 0

    completed_query = select(func.count()).where(
        PlanStep.plan_id == plan.id,
        PlanStep.status == PlanStepStatus.completed,
    )
    completed_result = await db.execute(completed_query)
    completed_steps = completed_result.scalar() or 0

    # If all steps are completed, mark plan as completed
    if total_steps > 0 and total_steps == completed_steps:
        plan.status = PlanStatus.completed
        await db.flush()

    # Update goal progress if plan is linked to a goal
    if plan.goal_id is not None:
        await update_goal_progress(db, plan)


async def update_goal_progress(db: AsyncSession, plan: Plan) -> None:
    """Recalculate goal progress based on plan completion status.

    Progress is calculated as: (completed plans / total plans) * 100

    Args:
        db: Database session.
        plan: The Plan that triggered the recalculation.
    """
    if plan.goal_id is None:
        return

    goal_query = select(Goal).where(Goal.id == plan.goal_id)
    goal_result = await db.execute(goal_query)
    goal = goal_result.scalar_one_or_none()

    if goal is None:
        return

    # Count total and completed plans for this goal
    total_plans_query = select(func.count()).where(Plan.goal_id == goal.id)
    total_result = await db.execute(total_plans_query)
    total_plans = total_result.scalar() or 0

    completed_plans_query = select(func.count()).where(
        Plan.goal_id == goal.id,
        Plan.status == PlanStatus.completed,
    )
    completed_result = await db.execute(completed_plans_query)
    completed_plans = completed_result.scalar() or 0

    # Calculate progress percentage
    if total_plans > 0:
        goal.progress = int((completed_plans / total_plans) * 100)
    else:
        goal.progress = 0

    # If progress reaches 100%, mark goal as completed
    if goal.progress >= 100:
        goal.status = GoalStatus.completed

    await db.flush()
