"""Goals API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_family, get_current_user, get_db
from app.models.action import Action
from app.models.family import FamilyMember
from app.models.goal import Goal, GoalStatus
from app.models.plan import Plan, PlanStep
from app.models.task import Task
from app.models.user import User
from app.models.wish import Wish
from app.schemas.goal import (
    ChainActionItem,
    ChainPlanItem,
    ChainPlanStepItem,
    ChainTaskItem,
    ChainWishItem,
    GoalChainResponse,
    GoalCreateRequest,
    GoalListResponse,
    GoalResponse,
    GoalUpdateRequest,
)
from app.services.goal_service import (
    create_goal,
    delete_goal,
    get_goal_by_id,
    get_goals,
    update_goal,
)
from app.tasks.ai_tasks import generate_goal_smart

router = APIRouter()


@router.get("", response_model=GoalListResponse)
async def list_goals(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: GoalStatus | None = Query(None, alias="status", description="状态筛选"),
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of goals for the current user in their family."""
    goals, total = await get_goals(
        db=db,
        family_id=membership.family_id,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status_filter,
    )

    return GoalListResponse(
        items=[GoalResponse.model_validate(g) for g in goals],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal_endpoint(
    body: GoalCreateRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Create a new goal and trigger AI SMART generation."""
    # Validate wish_id if provided
    if body.wish_id is not None:
        wish_query = select(Wish).where(
            Wish.id == body.wish_id,
            Wish.family_id == membership.family_id,
        )
        result = await db.execute(wish_query)
        wish = result.scalar_one_or_none()
        if wish is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="关联的愿望不存在",
            )

    goal = await create_goal(
        db=db,
        family_id=membership.family_id,
        user_id=current_user.id,
        title=body.title,
        description=body.description,
        wish_id=body.wish_id,
    )

    # Trigger async AI generation task (SMART description + cover image)
    generate_goal_smart.delay(str(goal.id))

    return GoalResponse.model_validate(goal)


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get a single goal by ID."""
    goal = await get_goal_by_id(db=db, goal_id=goal_id, family_id=membership.family_id)
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目标不存在",
        )
    return GoalResponse.model_validate(goal)


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal_endpoint(
    goal_id: uuid.UUID,
    body: GoalUpdateRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Update a goal. If title changes, triggers AI regeneration."""
    goal = await get_goal_by_id(db=db, goal_id=goal_id, family_id=membership.family_id)
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目标不存在",
        )

    # Only the creator can update
    if goal.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有创建者可以编辑目标",
        )

    title_changed = body.title is not None and body.title != goal.title

    goal = await update_goal(
        db=db,
        goal=goal,
        title=body.title,
        description=body.description,
        status=body.status,
        progress=body.progress,
    )

    # If title changed, regenerate AI content
    if title_changed:
        generate_goal_smart.delay(str(goal.id))

    return GoalResponse.model_validate(goal)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal_endpoint(
    goal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Delete a goal. Only the creator can delete."""
    goal = await get_goal_by_id(db=db, goal_id=goal_id, family_id=membership.family_id)
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目标不存在",
        )

    if goal.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有创建者可以删除目标",
        )

    await delete_goal(db=db, goal=goal)


@router.get("/{goal_id}/chain", response_model=GoalChainResponse)
async def get_goal_chain(
    goal_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get the full chain for a goal: wish → goal → plans → tasks → actions."""
    goal = await get_goal_by_id(db=db, goal_id=goal_id, family_id=membership.family_id)
    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="目标不存在",
        )

    # Get associated wish
    chain_wish = None
    if goal.wish_id is not None:
        wish_result = await db.execute(
            select(Wish).where(Wish.id == goal.wish_id)
        )
        wish = wish_result.scalar_one_or_none()
        if wish:
            chain_wish = ChainWishItem.model_validate(wish)

    # Get plans associated with this goal
    plans_result = await db.execute(
        select(Plan).where(Plan.goal_id == goal_id).order_by(Plan.created_at.desc())
    )
    plans = list(plans_result.scalars().all())

    chain_plans: list[ChainPlanItem] = []
    for plan in plans:
        # Get plan steps
        steps_result = await db.execute(
            select(PlanStep)
            .where(PlanStep.plan_id == plan.id)
            .order_by(PlanStep.sort_order)
        )
        steps = list(steps_result.scalars().all())

        chain_steps = [ChainPlanStepItem.model_validate(s) for s in steps]

        # Get tasks associated with this plan's steps
        step_ids = [s.id for s in steps]
        chain_tasks: list[ChainTaskItem] = []
        if step_ids:
            tasks_result = await db.execute(
                select(Task).where(Task.plan_step_id.in_(step_ids))
            )
            tasks = list(tasks_result.scalars().all())

            for task in tasks:
                # Get actions associated with this task
                actions_result = await db.execute(
                    select(Action).where(Action.task_id == task.id)
                )
                actions = list(actions_result.scalars().all())
                chain_actions = [ChainActionItem.model_validate(a) for a in actions]

                chain_tasks.append(
                    ChainTaskItem(
                        id=task.id,
                        title=task.title,
                        cover_image_url=task.cover_image_url,
                        display_text=task.display_text,
                        task_type=task.task_type.value,
                        status=task.status.value,
                        reward_points=task.reward_points,
                        penalty_points=task.penalty_points,
                        actions=chain_actions,
                    )
                )

        chain_plans.append(
            ChainPlanItem(
                id=plan.id,
                title=plan.title,
                cover_image_url=plan.cover_image_url,
                display_text=plan.display_text,
                status=plan.status.value,
                start_date=plan.start_date.isoformat() if plan.start_date else None,
                end_date=plan.end_date.isoformat() if plan.end_date else None,
                steps=chain_steps,
                tasks=chain_tasks,
            )
        )

    return GoalChainResponse(
        wish=chain_wish,
        goal=GoalResponse.model_validate(goal),
        plans=chain_plans,
    )
