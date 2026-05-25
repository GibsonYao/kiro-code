"""Plans API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_family, get_current_user, get_db
from app.models.family import FamilyMember
from app.models.goal import Goal
from app.models.plan import PlanStatus
from app.models.user import User
from app.schemas.plan import (
    PlanCreateRequest,
    PlanListResponse,
    PlanResponse,
    PlanStepCreateRequest,
    PlanStepResponse,
    PlanStepUpdateRequest,
    PlanUpdateRequest,
)
from app.services.plan_service import (
    create_plan,
    create_plan_step,
    delete_plan,
    delete_plan_step,
    get_plan_by_id,
    get_plan_step_by_id,
    get_plans,
    update_plan,
    update_plan_step,
    validate_owner_is_family_member,
)

router = APIRouter()


@router.get("", response_model=PlanListResponse)
async def list_plans(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status_filter: PlanStatus | None = Query(None, alias="status", description="状态筛选"),
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of plans for the current family."""
    plans, total = await get_plans(
        db=db,
        family_id=membership.family_id,
        page=page,
        page_size=page_size,
        status=status_filter,
    )

    return PlanListResponse(
        items=[PlanResponse.model_validate(p) for p in plans],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan_endpoint(
    body: PlanCreateRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Create a new plan. Owner must be a member of the current family."""
    # Validate owner is a family member (Requirement 4.9)
    is_member = await validate_owner_is_family_member(
        db=db,
        owner_id=body.owner_id,
        family_id=membership.family_id,
    )
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="负责人必须是当前家庭成员",
        )

    # Validate goal_id if provided
    if body.goal_id is not None:
        goal_query = select(Goal).where(
            Goal.id == body.goal_id,
            Goal.family_id == membership.family_id,
        )
        result = await db.execute(goal_query)
        goal = result.scalar_one_or_none()
        if goal is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="关联的目标不存在",
            )

    plan = await create_plan(
        db=db,
        family_id=membership.family_id,
        title=body.title,
        owner_id=body.owner_id,
        goal_id=body.goal_id,
        start_date=body.start_date,
        end_date=body.end_date,
    )

    # Newly created plan has no steps, construct response directly
    response_data = {
        "id": plan.id,
        "family_id": plan.family_id,
        "goal_id": plan.goal_id,
        "title": plan.title,
        "cover_image_url": plan.cover_image_url,
        "display_text": plan.display_text,
        "start_date": plan.start_date,
        "end_date": plan.end_date,
        "owner_id": plan.owner_id,
        "status": plan.status,
        "created_at": plan.created_at,
        "updated_at": plan.updated_at,
        "steps": [],
    }
    return PlanResponse.model_validate(response_data)


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Get a single plan by ID."""
    plan = await get_plan_by_id(db=db, plan_id=plan_id, family_id=membership.family_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="计划不存在",
        )
    return PlanResponse.model_validate(plan)


@router.put("/{plan_id}", response_model=PlanResponse)
async def update_plan_endpoint(
    plan_id: uuid.UUID,
    body: PlanUpdateRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Update a plan."""
    plan = await get_plan_by_id(db=db, plan_id=plan_id, family_id=membership.family_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="计划不存在",
        )

    # Validate new owner if provided
    if body.owner_id is not None:
        is_member = await validate_owner_is_family_member(
            db=db,
            owner_id=body.owner_id,
            family_id=membership.family_id,
        )
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="负责人必须是当前家庭成员",
            )

    plan = await update_plan(
        db=db,
        plan=plan,
        title=body.title,
        start_date=body.start_date,
        end_date=body.end_date,
        owner_id=body.owner_id,
        status=body.status,
    )

    return PlanResponse.model_validate(plan)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan_endpoint(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Delete a plan. Only the owner or family admin can delete."""
    plan = await get_plan_by_id(db=db, plan_id=plan_id, family_id=membership.family_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="计划不存在",
        )

    # Only owner or family admin can delete
    if plan.owner_id != current_user.id and membership.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有负责人或家庭管理员可以删除计划",
        )

    await delete_plan(db=db, plan=plan)


# ─── Plan Steps Endpoints ──────────────────────────────────────────────────────


@router.post("/{plan_id}/steps", response_model=PlanStepResponse, status_code=status.HTTP_201_CREATED)
async def create_step_endpoint(
    plan_id: uuid.UUID,
    body: PlanStepCreateRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Add a step to a plan."""
    plan = await get_plan_by_id(db=db, plan_id=plan_id, family_id=membership.family_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="计划不存在",
        )

    step = await create_plan_step(
        db=db,
        plan_id=plan_id,
        title=body.title,
        step_type=body.step_type,
        is_bounty=body.is_bounty,
        sort_order=body.sort_order,
    )

    return PlanStepResponse.model_validate(step)


@router.put("/{plan_id}/steps/{step_id}", response_model=PlanStepResponse)
async def update_step_endpoint(
    plan_id: uuid.UUID,
    step_id: uuid.UUID,
    body: PlanStepUpdateRequest,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Update a plan step."""
    # Verify plan exists and belongs to family
    plan = await get_plan_by_id(db=db, plan_id=plan_id, family_id=membership.family_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="计划不存在",
        )

    step = await get_plan_step_by_id(db=db, step_id=step_id, plan_id=plan_id)
    if step is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="步骤不存在",
        )

    step = await update_plan_step(
        db=db,
        step=step,
        title=body.title,
        step_type=body.step_type,
        is_bounty=body.is_bounty,
        sort_order=body.sort_order,
        status=body.status,
    )

    return PlanStepResponse.model_validate(step)


@router.delete("/{plan_id}/steps/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_step_endpoint(
    plan_id: uuid.UUID,
    step_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    membership: FamilyMember = Depends(get_current_family),
    db: AsyncSession = Depends(get_db),
):
    """Delete a plan step."""
    # Verify plan exists and belongs to family
    plan = await get_plan_by_id(db=db, plan_id=plan_id, family_id=membership.family_id)
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="计划不存在",
        )

    step = await get_plan_step_by_id(db=db, step_id=step_id, plan_id=plan_id)
    if step is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="步骤不存在",
        )

    await delete_plan_step(db=db, step=step)
