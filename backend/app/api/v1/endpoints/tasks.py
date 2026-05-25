"""Tasks API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_family, get_current_user, get_db
from app.models.family import FamilyMember
from app.models.review import Review, ReviewStatus, ReviewTargetType
from app.models.task import TaskStatus
from app.models.user import User
from app.schemas.task import (
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskSubmitRequest,
    TaskUpdateRequest,
)
from app.services.task_service import (
    claim_task,
    create_task,
    delete_task,
    get_bounty_tasks,
    get_task_by_id,
    get_tasks,
    submit_task,
    update_task,
)

router = APIRouter()


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: TaskStatus | None = Query(None, alias="status", description="状态筛选"),
    assignee_id: uuid.UUID | None = Query(None, description="指派人筛选"),
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of tasks for the current family."""
    tasks, total = await get_tasks(
        db=db,
        family_id=membership.family_id,
        page=page,
        page_size=page_size,
        status=status_filter,
        assignee_id=assignee_id,
    )

    return TaskListResponse(
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task_endpoint(
    body: TaskCreateRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Create a new task."""
    task = await create_task(
        db=db,
        family_id=membership.family_id,
        title=body.title,
        description=body.description,
        plan_step_id=body.plan_step_id,
        task_type=body.task_type,
        recurrence_rule=body.recurrence_rule,
        time_limit_hours=body.time_limit_hours,
        reward_points=body.reward_points,
        penalty_points=body.penalty_points,
        assignee_id=body.assignee_id,
    )

    return TaskResponse.model_validate(task)


@router.get("/bounty", response_model=TaskListResponse)
async def list_bounty_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of claimable bounty tasks."""
    tasks, total = await get_bounty_tasks(
        db=db,
        family_id=membership.family_id,
        page=page,
        page_size=page_size,
    )

    return TaskListResponse(
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get a single task by ID."""
    task = await get_task_by_id(db=db, task_id=task_id, family_id=membership.family_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )
    return TaskResponse.model_validate(task)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task_endpoint(
    task_id: uuid.UUID,
    body: TaskUpdateRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Update a task."""
    task = await get_task_by_id(db=db, task_id=task_id, family_id=membership.family_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )

    task = await update_task(
        db=db,
        task=task,
        title=body.title,
        description=body.description,
        task_type=body.task_type,
        recurrence_rule=body.recurrence_rule,
        time_limit_hours=body.time_limit_hours,
        reward_points=body.reward_points,
        penalty_points=body.penalty_points,
        assignee_id=body.assignee_id,
        status=body.status,
    )

    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_endpoint(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Delete a task. Only the creator or family admin can delete."""
    task = await get_task_by_id(db=db, task_id=task_id, family_id=membership.family_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )

    # Only family admin or assignee can delete
    if membership.role.value != "admin" and task.assignee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有家庭管理员或任务负责人可以删除任务",
        )

    await delete_task(db=db, task=task)


@router.post("/{task_id}/claim", response_model=TaskResponse)
async def claim_task_endpoint(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Claim a bounty task. Uses SELECT FOR UPDATE to prevent concurrent claims."""
    task = await claim_task(
        db=db,
        task_id=task_id,
        family_id=membership.family_id,
        user_id=current_user.id,
    )

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="任务不存在或已被认领",
        )

    return TaskResponse.model_validate(task)


@router.post("/{task_id}/submit", response_model=TaskResponse)
async def submit_task_endpoint(
    task_id: uuid.UUID,
    body: TaskSubmitRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Submit a task for review with evidence (text/photos/qrcode).

    At least one evidence type must be provided.
    """
    task = await get_task_by_id(db=db, task_id=task_id, family_id=membership.family_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在",
        )

    # Verify the task is in a submittable state
    if task.status not in (TaskStatus.claimed, TaskStatus.in_progress, TaskStatus.rejected):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前任务状态不允许提交",
        )

    # Verify the submitter is the assignee
    if task.assignee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有任务执行人可以提交完成",
        )

    # At least one evidence type must be provided
    if not body.evidence_text and not body.evidence_photos and not body.evidence_qrcode:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请提供至少一种完成验证要素（文字描述、照片或扫码）",
        )

    # Create a review record
    # Determine reviewer: plan owner > family admin
    reviewer_id = await _determine_reviewer(db, task, membership)

    review = Review(
        family_id=membership.family_id,
        target_type=ReviewTargetType.task,
        target_id=task.id,
        reviewer_id=reviewer_id,
        submitter_id=current_user.id,
        status=ReviewStatus.pending,
        evidence_text=body.evidence_text,
        evidence_photos=body.evidence_photos,
        evidence_qrcode=body.evidence_qrcode,
    )
    db.add(review)

    # Update task status to submitted
    task = await submit_task(db=db, task=task)

    return TaskResponse.model_validate(task)


async def _determine_reviewer(
    db: AsyncSession,
    task: "Task",
    membership: FamilyMember,
) -> uuid.UUID:
    """Determine the reviewer for a task submission.

    Priority:
    1. If task has a plan_step → plan owner
    2. Otherwise → family admin

    Args:
        db: Database session.
        task: The task being submitted.
        membership: Current user's family membership.

    Returns:
        UUID of the reviewer.
    """
    from sqlalchemy import select as sa_select

    from app.models.family import FamilyMember as FM
    from app.models.family import FamilyRole
    from app.models.plan import Plan, PlanStep

    # If task is linked to a plan step, find the plan owner
    if task.plan_step_id:
        step_query = sa_select(PlanStep).where(PlanStep.id == task.plan_step_id)
        step_result = await db.execute(step_query)
        step = step_result.scalar_one_or_none()

        if step:
            plan_query = sa_select(Plan).where(Plan.id == step.plan_id)
            plan_result = await db.execute(plan_query)
            plan = plan_result.scalar_one_or_none()

            if plan and plan.owner_id:
                return plan.owner_id

    # Fallback: family admin
    admin_query = sa_select(FM).where(
        FM.family_id == membership.family_id,
        FM.role == FamilyRole.admin,
    )
    admin_result = await db.execute(admin_query)
    admin = admin_result.scalar_one_or_none()

    if admin:
        return admin.user_id

    # Last resort: return the current user's ID (self-review edge case)
    return membership.user_id
