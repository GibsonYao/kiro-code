"""Actions API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_family, get_current_user, get_db
from app.models.action import ActionStatus, ActionType
from app.models.family import FamilyMember
from app.models.user import User
from app.schemas.action import (
    ActionCreateRequest,
    ActionListResponse,
    ActionResponse,
    ActionTimeLogRequest,
    ActionUpdateRequest,
)
from app.services.action_service import (
    complete_action,
    create_action,
    delete_action,
    get_action_by_id,
    get_actions,
    update_action,
    update_task_progress_on_action_complete,
    update_time_log,
)

router = APIRouter()


@router.get("", response_model=ActionListResponse)
async def list_actions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    action_type: ActionType | None = Query(None, description="行动类型筛选（todo/schedule）"),
    status_filter: ActionStatus | None = Query(None, alias="status", description="状态筛选"),
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of actions for the current family."""
    actions, total = await get_actions(
        db=db,
        family_id=membership.family_id,
        user_id=current_user.id,
        action_type=action_type,
        status=status_filter,
        page=page,
        page_size=page_size,
    )

    return ActionListResponse(
        items=[ActionResponse.model_validate(a) for a in actions],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.post("", response_model=ActionResponse, status_code=status.HTTP_201_CREATED)
async def create_action_endpoint(
    body: ActionCreateRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Create a new action."""
    action = await create_action(
        db=db,
        family_id=membership.family_id,
        user_id=current_user.id,
        title=body.title,
        action_type=body.action_type,
        task_id=body.task_id,
        plan_step_id=body.plan_step_id,
        scheduled_date=body.scheduled_date,
        scheduled_time=body.scheduled_time,
        reward_points=body.reward_points,
    )

    return ActionResponse.model_validate(action)


@router.get("/{action_id}", response_model=ActionResponse)
async def get_action(
    action_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get a single action by ID."""
    action = await get_action_by_id(db=db, action_id=action_id, family_id=membership.family_id)
    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行动不存在",
        )
    return ActionResponse.model_validate(action)


@router.put("/{action_id}", response_model=ActionResponse)
async def update_action_endpoint(
    action_id: uuid.UUID,
    body: ActionUpdateRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Update an action."""
    action = await get_action_by_id(db=db, action_id=action_id, family_id=membership.family_id)
    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行动不存在",
        )

    # Only the action owner can update
    if action.user_id != current_user.id and membership.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有行动创建者或家庭管理员可以修改行动",
        )

    action = await update_action(
        db=db,
        action=action,
        title=body.title,
        action_type=body.action_type,
        scheduled_date=body.scheduled_date,
        scheduled_time=body.scheduled_time,
        reward_points=body.reward_points,
        status=body.status,
    )

    return ActionResponse.model_validate(action)


@router.delete("/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action_endpoint(
    action_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Delete an action. Only the creator or family admin can delete."""
    action = await get_action_by_id(db=db, action_id=action_id, family_id=membership.family_id)
    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行动不存在",
        )

    # Only family admin or action owner can delete
    if action.user_id != current_user.id and membership.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有行动创建者或家庭管理员可以删除行动",
        )

    await delete_action(db=db, action=action)


@router.post("/{action_id}/complete", response_model=ActionResponse)
async def complete_action_endpoint(
    action_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Mark an action as completed (submitted for review).

    When an action is completed and linked to a task, the task's progress
    is automatically updated.
    """
    action = await get_action_by_id(db=db, action_id=action_id, family_id=membership.family_id)
    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行动不存在",
        )

    # Only the action owner can complete it
    if action.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有行动执行人可以标记完成",
        )

    # Verify the action is in a completable state
    if action.status not in (ActionStatus.pending, ActionStatus.in_progress, ActionStatus.rejected):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前行动状态不允许标记完成",
        )

    # Mark action as submitted
    action = await complete_action(db=db, action=action)

    # Update linked task progress
    await update_task_progress_on_action_complete(db=db, action=action)

    return ActionResponse.model_validate(action)


@router.put("/{action_id}/time-log", response_model=ActionResponse)
async def update_time_log_endpoint(
    action_id: uuid.UUID,
    body: ActionTimeLogRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Record time spent on an action."""
    action = await get_action_by_id(db=db, action_id=action_id, family_id=membership.family_id)
    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行动不存在",
        )

    # Only the action owner can log time
    if action.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有行动执行人可以记录时间",
        )

    action = await update_time_log(
        db=db,
        action=action,
        time_spent_minutes=body.time_spent_minutes,
    )

    return ActionResponse.model_validate(action)
