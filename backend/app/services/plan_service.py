"""Plan service layer — business logic for plan CRUD operations."""

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.family import FamilyMember
from app.models.plan import Plan, PlanStatus, PlanStep, PlanStepStatus, StepType


async def get_plans(
    db: AsyncSession,
    family_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
    status: PlanStatus | None = None,
) -> tuple[list[Plan], int]:
    """Get paginated list of plans for a family.

    Args:
        db: Database session.
        family_id: Family UUID to filter by.
        page: Page number (1-indexed).
        page_size: Number of items per page.
        status: Optional status filter.

    Returns:
        Tuple of (plans list, total count).
    """
    base_query = select(Plan).where(Plan.family_id == family_id)

    if status is not None:
        base_query = base_query.where(Plan.status == status)

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch paginated results with steps eagerly loaded
    offset = (page - 1) * page_size
    query = (
        base_query.options(selectinload(Plan.steps))
        .order_by(Plan.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    plans = list(result.scalars().unique().all())

    return plans, total


async def get_plan_by_id(
    db: AsyncSession,
    plan_id: uuid.UUID,
    family_id: uuid.UUID,
) -> Plan | None:
    """Get a single plan by ID, scoped to a family.

    Args:
        db: Database session.
        plan_id: Plan UUID.
        family_id: Family UUID for access control.

    Returns:
        Plan instance or None if not found.
    """
    query = (
        select(Plan)
        .options(selectinload(Plan.steps))
        .where(Plan.id == plan_id, Plan.family_id == family_id)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def validate_owner_is_family_member(
    db: AsyncSession,
    owner_id: uuid.UUID,
    family_id: uuid.UUID,
) -> bool:
    """Validate that the owner_id belongs to a member of the given family.

    Args:
        db: Database session.
        owner_id: User UUID to validate.
        family_id: Family UUID to check membership.

    Returns:
        True if the user is a member of the family, False otherwise.
    """
    query = select(FamilyMember).where(
        FamilyMember.user_id == owner_id,
        FamilyMember.family_id == family_id,
    )
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None


async def create_plan(
    db: AsyncSession,
    family_id: uuid.UUID,
    title: str,
    owner_id: uuid.UUID,
    goal_id: uuid.UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> Plan:
    """Create a new plan.

    Args:
        db: Database session.
        family_id: Family UUID.
        title: Plan title.
        owner_id: Owner user UUID.
        goal_id: Associated goal UUID (optional).
        start_date: Plan start date (optional).
        end_date: Plan end date (optional).

    Returns:
        Created Plan instance.
    """
    plan = Plan(
        family_id=family_id,
        goal_id=goal_id,
        title=title,
        owner_id=owner_id,
        start_date=start_date,
        end_date=end_date,
        status=PlanStatus.draft,
    )
    plan.steps = []  # Initialize empty steps to avoid lazy load issue
    db.add(plan)
    await db.flush()
    await db.refresh(plan)
    return plan


async def update_plan(
    db: AsyncSession,
    plan: Plan,
    title: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    owner_id: uuid.UUID | None = None,
    status: PlanStatus | None = None,
) -> Plan:
    """Update an existing plan.

    Args:
        db: Database session.
        plan: Plan instance to update.
        title: New title (optional).
        start_date: New start date (optional).
        end_date: New end date (optional).
        owner_id: New owner ID (optional).
        status: New status (optional).

    Returns:
        Updated Plan instance.
    """
    if title is not None:
        plan.title = title
    if start_date is not None:
        plan.start_date = start_date
    if end_date is not None:
        plan.end_date = end_date
    if owner_id is not None:
        plan.owner_id = owner_id
    if status is not None:
        plan.status = status

    await db.flush()
    await db.refresh(plan)
    return plan


async def delete_plan(db: AsyncSession, plan: Plan) -> None:
    """Delete a plan and its steps.

    Args:
        db: Database session.
        plan: Plan instance to delete.
    """
    await db.delete(plan)
    await db.flush()


# ─── Plan Step Operations ──────────────────────────────────────────────────────


async def get_plan_step_by_id(
    db: AsyncSession,
    step_id: uuid.UUID,
    plan_id: uuid.UUID,
) -> PlanStep | None:
    """Get a single plan step by ID, scoped to a plan.

    Args:
        db: Database session.
        step_id: PlanStep UUID.
        plan_id: Plan UUID for access control.

    Returns:
        PlanStep instance or None if not found.
    """
    query = select(PlanStep).where(
        PlanStep.id == step_id,
        PlanStep.plan_id == plan_id,
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_plan_step(
    db: AsyncSession,
    plan_id: uuid.UUID,
    title: str,
    step_type: StepType,
    is_bounty: bool = False,
    sort_order: int = 0,
) -> PlanStep:
    """Create a new plan step.

    Args:
        db: Database session.
        plan_id: Plan UUID.
        title: Step title.
        step_type: Step type (task/action).
        is_bounty: Whether this is a bounty task.
        sort_order: Sort order.

    Returns:
        Created PlanStep instance.
    """
    step = PlanStep(
        plan_id=plan_id,
        title=title,
        step_type=step_type,
        is_bounty=is_bounty,
        sort_order=sort_order,
        status=PlanStepStatus.pending,
    )
    db.add(step)
    await db.flush()
    await db.refresh(step)
    return step


async def update_plan_step(
    db: AsyncSession,
    step: PlanStep,
    title: str | None = None,
    step_type: StepType | None = None,
    is_bounty: bool | None = None,
    sort_order: int | None = None,
    status: PlanStepStatus | None = None,
) -> PlanStep:
    """Update an existing plan step.

    Args:
        db: Database session.
        step: PlanStep instance to update.
        title: New title (optional).
        step_type: New step type (optional).
        is_bounty: New bounty flag (optional).
        sort_order: New sort order (optional).
        status: New status (optional).

    Returns:
        Updated PlanStep instance.
    """
    if title is not None:
        step.title = title
    if step_type is not None:
        step.step_type = step_type
    if is_bounty is not None:
        step.is_bounty = is_bounty
    if sort_order is not None:
        step.sort_order = sort_order
    if status is not None:
        step.status = status

    await db.flush()
    await db.refresh(step)
    return step


async def delete_plan_step(db: AsyncSession, step: PlanStep) -> None:
    """Delete a plan step.

    Args:
        db: Database session.
        step: PlanStep instance to delete.
    """
    await db.delete(step)
    await db.flush()
