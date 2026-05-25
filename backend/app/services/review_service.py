"""Review service layer — business logic for the review/approval workflow.

Implements the reviewer determination logic:
  Plan owner > Goal owner > Family admin

When a task or action is submitted for review, this service determines
the appropriate reviewer and creates a Review record.
"""

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import Action, ActionStatus
from app.models.family import FamilyMember, FamilyRole
from app.models.goal import Goal
from app.models.plan import Plan, PlanStep
from app.models.review import Review, ReviewStatus, ReviewTargetType
from app.models.task import Task, TaskStatus

logger = logging.getLogger(__name__)


async def determine_reviewer_for_task(
    db: AsyncSession,
    task: Task,
    family_id: uuid.UUID,
) -> uuid.UUID | None:
    """Determine the reviewer for a task based on the hierarchy.

    Priority:
      1. Plan owner (if task is linked to a plan step)
      2. Goal owner (if the plan is linked to a goal)
      3. Family admin

    Args:
        db: Database session.
        task: The task being submitted for review.
        family_id: Family UUID for finding the admin fallback.

    Returns:
        The reviewer's user UUID, or None if no reviewer can be determined.
    """
    # 1. Check if task is linked to a plan step → get plan owner
    if task.plan_step_id is not None:
        step_query = select(PlanStep).where(PlanStep.id == task.plan_step_id)
        step_result = await db.execute(step_query)
        plan_step = step_result.scalar_one_or_none()

        if plan_step is not None:
            plan_query = select(Plan).where(Plan.id == plan_step.plan_id)
            plan_result = await db.execute(plan_query)
            plan = plan_result.scalar_one_or_none()

            if plan is not None:
                # Plan owner is the reviewer (if different from submitter)
                if plan.owner_id != task.assignee_id:
                    return plan.owner_id

                # 2. If plan owner is the submitter, try goal owner
                if plan.goal_id is not None:
                    goal_query = select(Goal).where(Goal.id == plan.goal_id)
                    goal_result = await db.execute(goal_query)
                    goal = goal_result.scalar_one_or_none()

                    if goal is not None and goal.owner_id != task.assignee_id:
                        return goal.owner_id

    # 3. Fallback to family admin
    return await _get_family_admin_user_id(db, family_id, exclude_user_id=task.assignee_id)


async def determine_reviewer_for_action(
    db: AsyncSession,
    action: Action,
    family_id: uuid.UUID,
) -> uuid.UUID | None:
    """Determine the reviewer for an action based on the hierarchy.

    Priority:
      1. Plan owner (if action is linked to a plan step, or linked task has a plan step)
      2. Goal owner (if the plan is linked to a goal)
      3. Family admin

    Args:
        db: Database session.
        action: The action being submitted for review.
        family_id: Family UUID for finding the admin fallback.

    Returns:
        The reviewer's user UUID, or None if no reviewer can be determined.
    """
    submitter_id = action.user_id

    # Try to find plan step from action directly or via linked task
    plan_step_id = action.plan_step_id

    if plan_step_id is None and action.task_id is not None:
        # Get the linked task's plan_step_id
        task_query = select(Task).where(Task.id == action.task_id)
        task_result = await db.execute(task_query)
        task = task_result.scalar_one_or_none()
        if task is not None:
            plan_step_id = task.plan_step_id

    # 1. Check plan step → plan owner
    if plan_step_id is not None:
        step_query = select(PlanStep).where(PlanStep.id == plan_step_id)
        step_result = await db.execute(step_query)
        plan_step = step_result.scalar_one_or_none()

        if plan_step is not None:
            plan_query = select(Plan).where(Plan.id == plan_step.plan_id)
            plan_result = await db.execute(plan_query)
            plan = plan_result.scalar_one_or_none()

            if plan is not None:
                # Plan owner is the reviewer (if different from submitter)
                if plan.owner_id != submitter_id:
                    return plan.owner_id

                # 2. If plan owner is the submitter, try goal owner
                if plan.goal_id is not None:
                    goal_query = select(Goal).where(Goal.id == plan.goal_id)
                    goal_result = await db.execute(goal_query)
                    goal = goal_result.scalar_one_or_none()

                    if goal is not None and goal.owner_id != submitter_id:
                        return goal.owner_id

    # 3. Fallback to family admin
    return await _get_family_admin_user_id(db, family_id, exclude_user_id=submitter_id)


async def _get_family_admin_user_id(
    db: AsyncSession,
    family_id: uuid.UUID,
    exclude_user_id: uuid.UUID | None = None,
) -> uuid.UUID | None:
    """Get the family admin's user ID.

    If the admin is the same as the excluded user (submitter), still return
    the admin since there's no other option.

    Args:
        db: Database session.
        family_id: Family UUID.
        exclude_user_id: User to try to exclude (the submitter).

    Returns:
        Admin user UUID, or None if no admin found.
    """
    # First try to find an admin that is NOT the submitter
    if exclude_user_id is not None:
        query = select(FamilyMember).where(
            FamilyMember.family_id == family_id,
            FamilyMember.role == FamilyRole.admin,
            FamilyMember.user_id != exclude_user_id,
        )
        result = await db.execute(query)
        admin_member = result.scalars().first()
        if admin_member is not None:
            return admin_member.user_id

    # If no other admin, return any admin (even if it's the submitter)
    query = select(FamilyMember).where(
        FamilyMember.family_id == family_id,
        FamilyMember.role == FamilyRole.admin,
    )
    result = await db.execute(query)
    admin_member = result.scalars().first()
    return admin_member.user_id if admin_member is not None else None


async def create_review_for_task(
    db: AsyncSession,
    task: Task,
    family_id: uuid.UUID,
    evidence_text: str | None = None,
    evidence_photos: list | None = None,
    evidence_qrcode: str | None = None,
) -> Review | None:
    """Create a review record when a task is submitted.

    Determines the reviewer automatically and creates the Review.

    Args:
        db: Database session.
        task: The submitted task.
        family_id: Family UUID.
        evidence_text: Text evidence for completion.
        evidence_photos: Photo URLs as evidence.
        evidence_qrcode: QR code scan evidence.

    Returns:
        Created Review instance, or None if no reviewer could be determined.
    """
    reviewer_id = await determine_reviewer_for_task(db, task, family_id)
    if reviewer_id is None:
        return None

    review = Review(
        family_id=family_id,
        target_type=ReviewTargetType.task,
        target_id=task.id,
        reviewer_id=reviewer_id,
        submitter_id=task.assignee_id,
        status=ReviewStatus.pending,
        evidence_text=evidence_text,
        evidence_photos=evidence_photos,
        evidence_qrcode=evidence_qrcode,
    )
    db.add(review)
    await db.flush()
    await db.refresh(review)
    return review


async def create_review_for_action(
    db: AsyncSession,
    action: Action,
    family_id: uuid.UUID,
    evidence_text: str | None = None,
    evidence_photos: list | None = None,
    evidence_qrcode: str | None = None,
) -> Review | None:
    """Create a review record when an action is submitted.

    Determines the reviewer automatically and creates the Review.

    Args:
        db: Database session.
        action: The submitted action.
        family_id: Family UUID.
        evidence_text: Text evidence for completion.
        evidence_photos: Photo URLs as evidence.
        evidence_qrcode: QR code scan evidence.

    Returns:
        Created Review instance, or None if no reviewer could be determined.
    """
    reviewer_id = await determine_reviewer_for_action(db, action, family_id)
    if reviewer_id is None:
        return None

    review = Review(
        family_id=family_id,
        target_type=ReviewTargetType.action,
        target_id=action.id,
        reviewer_id=reviewer_id,
        submitter_id=action.user_id,
        status=ReviewStatus.pending,
        evidence_text=evidence_text,
        evidence_photos=evidence_photos,
        evidence_qrcode=evidence_qrcode,
    )
    db.add(review)
    await db.flush()
    await db.refresh(review)
    return review


async def get_pending_reviews(
    db: AsyncSession,
    family_id: uuid.UUID,
    reviewer_id: uuid.UUID,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Review], int]:
    """Get paginated list of pending reviews for a reviewer.

    Args:
        db: Database session.
        family_id: Family UUID.
        reviewer_id: Reviewer's user UUID.
        page: Page number (1-indexed).
        page_size: Number of items per page.

    Returns:
        Tuple of (reviews list, total count).
    """
    from sqlalchemy import func

    base_query = select(Review).where(
        Review.family_id == family_id,
        Review.reviewer_id == reviewer_id,
        Review.status == ReviewStatus.pending,
    )

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch paginated results
    offset = (page - 1) * page_size
    query = base_query.order_by(Review.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    reviews = list(result.scalars().all())

    return reviews, total


async def get_review_by_id(
    db: AsyncSession,
    review_id: uuid.UUID,
    family_id: uuid.UUID,
) -> Review | None:
    """Get a single review by ID, scoped to a family.

    Args:
        db: Database session.
        review_id: Review UUID.
        family_id: Family UUID for access control.

    Returns:
        Review instance or None if not found.
    """
    query = select(Review).where(Review.id == review_id, Review.family_id == family_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def approve_review(
    db: AsyncSession,
    review: Review,
    comment: str | None = None,
) -> Review:
    """Approve a review and update the target entity status.

    After updating the status, triggers chain propagation:
    - Awards points to the assignee/user
    - Propagates status up the goal management chain

    Args:
        db: Database session.
        review: Review instance to approve.
        comment: Optional approval comment.

    Returns:
        Updated Review instance.
    """
    from app.services.chain_propagation_service import (
        propagate_action_approval,
        propagate_task_approval,
    )

    review.status = ReviewStatus.approved
    if comment is not None:
        review.comment = comment

    # Update the target entity status and trigger chain propagation
    if review.target_type == ReviewTargetType.task:
        task_query = select(Task).where(Task.id == review.target_id)
        task_result = await db.execute(task_query)
        task = task_result.scalar_one_or_none()
        if task is not None:
            task.status = TaskStatus.approved
            await db.flush()
            await propagate_task_approval(db, task)

    elif review.target_type == ReviewTargetType.action:
        action_query = select(Action).where(Action.id == review.target_id)
        action_result = await db.execute(action_query)
        action = action_result.scalar_one_or_none()
        if action is not None:
            action.status = ActionStatus.approved
            await db.flush()
            await propagate_action_approval(db, action)

    await db.flush()
    await db.refresh(review)
    return review


async def notify_rejection(db: AsyncSession, review: Review) -> None:
    """Notify the submitter that their submission was rejected.

    This is a placeholder for the full notification system (Task 19).
    Currently logs the rejection event so it can be expanded later.

    Args:
        db: Database session (reserved for future notification persistence).
        review: The rejected Review instance.
    """
    # TODO: Replace with full notification dispatch once NotificationService is implemented (Task 19)
    logger.info(
        "Review rejected: review_id=%s, target_type=%s, target_id=%s, "
        "submitter_id=%s, reviewer_id=%s, comment=%s",
        review.id,
        review.target_type.value if review.target_type else None,
        review.target_id,
        review.submitter_id,
        review.reviewer_id,
        review.comment,
    )


async def reject_review(
    db: AsyncSession,
    review: Review,
    comment: str | None = None,
) -> Review:
    """Reject a review and revert the target entity status to in_progress.

    Args:
        db: Database session.
        review: Review instance to reject.
        comment: Optional rejection reason.

    Returns:
        Updated Review instance.
    """
    review.status = ReviewStatus.rejected
    if comment is not None:
        review.comment = comment

    # Revert the target entity status to in_progress
    if review.target_type == ReviewTargetType.task:
        task_query = select(Task).where(Task.id == review.target_id)
        task_result = await db.execute(task_query)
        task = task_result.scalar_one_or_none()
        if task is not None:
            task.status = TaskStatus.in_progress

    elif review.target_type == ReviewTargetType.action:
        action_query = select(Action).where(Action.id == review.target_id)
        action_result = await db.execute(action_query)
        action = action_result.scalar_one_or_none()
        if action is not None:
            action.status = ActionStatus.in_progress

    await db.flush()
    await db.refresh(review)

    # Notify the submitter about the rejection
    await notify_rejection(db, review)

    return review
