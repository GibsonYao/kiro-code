"""Tests for the review service layer — reviewer determination and review lifecycle."""

import uuid

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.action import Action, ActionStatus, ActionType
from app.models.family import Family, FamilyMember, FamilyRole
from app.models.goal import Goal, GoalStatus
from app.models.plan import Plan, PlanStatus, PlanStep, PlanStepStatus, StepType
from app.models.review import Review, ReviewStatus, ReviewTargetType
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.services.review_service import (
    approve_review,
    create_review_for_action,
    create_review_for_task,
    determine_reviewer_for_action,
    determine_reviewer_for_task,
    get_pending_reviews,
    get_review_by_id,
    reject_review,
)


# ─── Test Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
async def db_session():
    """Create an in-memory SQLite async session for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def user_ids():
    """Generate fixed UUIDs for test users."""
    return {
        "admin": uuid.uuid4(),
        "member1": uuid.uuid4(),
        "member2": uuid.uuid4(),
        "plan_owner": uuid.uuid4(),
        "goal_owner": uuid.uuid4(),
    }


@pytest.fixture
def family_id():
    """Generate a fixed UUID for the test family."""
    return uuid.uuid4()


@pytest.fixture
async def setup_family(db_session: AsyncSession, user_ids, family_id):
    """Set up a family with admin and members."""
    # Create users
    for key, uid in user_ids.items():
        user = User(id=uid, nickname=key)
        db_session.add(user)

    # Create family
    family = Family(
        id=family_id,
        name="Test Family",
        invite_code="TEST123",
        created_by=user_ids["admin"],
    )
    db_session.add(family)

    # Create family members
    admin_member = FamilyMember(
        family_id=family_id,
        user_id=user_ids["admin"],
        role=FamilyRole.admin,
        nickname_in_family="Admin",
    )
    db_session.add(admin_member)

    for key in ["member1", "member2", "plan_owner", "goal_owner"]:
        member = FamilyMember(
            family_id=family_id,
            user_id=user_ids[key],
            role=FamilyRole.member,
            nickname_in_family=key,
        )
        db_session.add(member)

    await db_session.flush()
    return family


# ─── Reviewer Determination Tests (Task) ──────────────────────────────────────


class TestDetermineReviewerForTask:
    """Test reviewer determination logic for tasks."""

    @pytest.mark.asyncio
    async def test_task_with_plan_step_returns_plan_owner(
        self, db_session, user_ids, family_id, setup_family
    ):
        """When task is linked to a plan step, plan owner should be reviewer."""
        # Create goal and plan
        goal = Goal(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_ids["goal_owner"],
            title="Test Goal",
            owner_id=user_ids["goal_owner"],
        )
        db_session.add(goal)

        plan = Plan(
            id=uuid.uuid4(),
            family_id=family_id,
            goal_id=goal.id,
            title="Test Plan",
            owner_id=user_ids["plan_owner"],
        )
        db_session.add(plan)

        plan_step = PlanStep(
            id=uuid.uuid4(),
            plan_id=plan.id,
            title="Step 1",
            step_type=StepType.task,
        )
        db_session.add(plan_step)

        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            plan_step_id=plan_step.id,
            title="Test Task",
            task_type=TaskType.once,
            assignee_id=user_ids["member1"],
            status=TaskStatus.submitted,
        )
        db_session.add(task)
        await db_session.flush()

        reviewer_id = await determine_reviewer_for_task(db_session, task, family_id)
        assert reviewer_id == user_ids["plan_owner"]

    @pytest.mark.asyncio
    async def test_task_plan_owner_is_submitter_falls_to_goal_owner(
        self, db_session, user_ids, family_id, setup_family
    ):
        """When plan owner is the task assignee, fall back to goal owner."""
        goal = Goal(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_ids["goal_owner"],
            title="Test Goal",
            owner_id=user_ids["goal_owner"],
        )
        db_session.add(goal)

        plan = Plan(
            id=uuid.uuid4(),
            family_id=family_id,
            goal_id=goal.id,
            title="Test Plan",
            owner_id=user_ids["plan_owner"],
        )
        db_session.add(plan)

        plan_step = PlanStep(
            id=uuid.uuid4(),
            plan_id=plan.id,
            title="Step 1",
            step_type=StepType.task,
        )
        db_session.add(plan_step)

        # Task assignee IS the plan owner
        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            plan_step_id=plan_step.id,
            title="Test Task",
            task_type=TaskType.once,
            assignee_id=user_ids["plan_owner"],
            status=TaskStatus.submitted,
        )
        db_session.add(task)
        await db_session.flush()

        reviewer_id = await determine_reviewer_for_task(db_session, task, family_id)
        assert reviewer_id == user_ids["goal_owner"]

    @pytest.mark.asyncio
    async def test_task_no_plan_step_falls_to_family_admin(
        self, db_session, user_ids, family_id, setup_family
    ):
        """When task has no plan step, fall back to family admin."""
        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            plan_step_id=None,
            title="Standalone Task",
            task_type=TaskType.once,
            assignee_id=user_ids["member1"],
            status=TaskStatus.submitted,
        )
        db_session.add(task)
        await db_session.flush()

        reviewer_id = await determine_reviewer_for_task(db_session, task, family_id)
        assert reviewer_id == user_ids["admin"]

    @pytest.mark.asyncio
    async def test_task_plan_no_goal_falls_to_family_admin(
        self, db_session, user_ids, family_id, setup_family
    ):
        """When plan has no goal and plan owner is submitter, fall back to admin."""
        plan = Plan(
            id=uuid.uuid4(),
            family_id=family_id,
            goal_id=None,
            title="Plan without Goal",
            owner_id=user_ids["plan_owner"],
        )
        db_session.add(plan)

        plan_step = PlanStep(
            id=uuid.uuid4(),
            plan_id=plan.id,
            title="Step 1",
            step_type=StepType.task,
        )
        db_session.add(plan_step)

        # Task assignee IS the plan owner, no goal to fall back to
        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            plan_step_id=plan_step.id,
            title="Test Task",
            task_type=TaskType.once,
            assignee_id=user_ids["plan_owner"],
            status=TaskStatus.submitted,
        )
        db_session.add(task)
        await db_session.flush()

        reviewer_id = await determine_reviewer_for_task(db_session, task, family_id)
        assert reviewer_id == user_ids["admin"]


# ─── Reviewer Determination Tests (Action) ────────────────────────────────────


class TestDetermineReviewerForAction:
    """Test reviewer determination logic for actions."""

    @pytest.mark.asyncio
    async def test_action_with_plan_step_returns_plan_owner(
        self, db_session, user_ids, family_id, setup_family
    ):
        """When action is linked to a plan step, plan owner should be reviewer."""
        plan = Plan(
            id=uuid.uuid4(),
            family_id=family_id,
            goal_id=None,
            title="Test Plan",
            owner_id=user_ids["plan_owner"],
        )
        db_session.add(plan)

        plan_step = PlanStep(
            id=uuid.uuid4(),
            plan_id=plan.id,
            title="Step 1",
            step_type=StepType.action,
        )
        db_session.add(plan_step)

        action = Action(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_ids["member1"],
            plan_step_id=plan_step.id,
            title="Test Action",
            action_type=ActionType.todo,
            status=ActionStatus.submitted,
        )
        db_session.add(action)
        await db_session.flush()

        reviewer_id = await determine_reviewer_for_action(db_session, action, family_id)
        assert reviewer_id == user_ids["plan_owner"]

    @pytest.mark.asyncio
    async def test_action_linked_to_task_uses_task_plan_step(
        self, db_session, user_ids, family_id, setup_family
    ):
        """When action is linked to a task with plan step, use task's plan step."""
        plan = Plan(
            id=uuid.uuid4(),
            family_id=family_id,
            goal_id=None,
            title="Test Plan",
            owner_id=user_ids["plan_owner"],
        )
        db_session.add(plan)

        plan_step = PlanStep(
            id=uuid.uuid4(),
            plan_id=plan.id,
            title="Step 1",
            step_type=StepType.task,
        )
        db_session.add(plan_step)

        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            plan_step_id=plan_step.id,
            title="Linked Task",
            task_type=TaskType.once,
            assignee_id=user_ids["member1"],
            status=TaskStatus.in_progress,
        )
        db_session.add(task)

        # Action linked to task but no direct plan_step_id
        action = Action(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_ids["member1"],
            task_id=task.id,
            plan_step_id=None,
            title="Test Action",
            action_type=ActionType.todo,
            status=ActionStatus.submitted,
        )
        db_session.add(action)
        await db_session.flush()

        reviewer_id = await determine_reviewer_for_action(db_session, action, family_id)
        assert reviewer_id == user_ids["plan_owner"]

    @pytest.mark.asyncio
    async def test_action_no_links_falls_to_family_admin(
        self, db_session, user_ids, family_id, setup_family
    ):
        """When action has no plan step or task link, fall back to family admin."""
        action = Action(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_ids["member1"],
            task_id=None,
            plan_step_id=None,
            title="Standalone Action",
            action_type=ActionType.todo,
            status=ActionStatus.submitted,
        )
        db_session.add(action)
        await db_session.flush()

        reviewer_id = await determine_reviewer_for_action(db_session, action, family_id)
        assert reviewer_id == user_ids["admin"]

    @pytest.mark.asyncio
    async def test_action_plan_owner_is_submitter_falls_to_goal_owner(
        self, db_session, user_ids, family_id, setup_family
    ):
        """When plan owner is the action submitter, fall back to goal owner."""
        goal = Goal(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_ids["goal_owner"],
            title="Test Goal",
            owner_id=user_ids["goal_owner"],
        )
        db_session.add(goal)

        plan = Plan(
            id=uuid.uuid4(),
            family_id=family_id,
            goal_id=goal.id,
            title="Test Plan",
            owner_id=user_ids["plan_owner"],
        )
        db_session.add(plan)

        plan_step = PlanStep(
            id=uuid.uuid4(),
            plan_id=plan.id,
            title="Step 1",
            step_type=StepType.action,
        )
        db_session.add(plan_step)

        # Action submitter IS the plan owner
        action = Action(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_ids["plan_owner"],
            plan_step_id=plan_step.id,
            title="Test Action",
            action_type=ActionType.todo,
            status=ActionStatus.submitted,
        )
        db_session.add(action)
        await db_session.flush()

        reviewer_id = await determine_reviewer_for_action(db_session, action, family_id)
        assert reviewer_id == user_ids["goal_owner"]


# ─── Review Creation Tests ─────────────────────────────────────────────────────


class TestCreateReviewForTask:
    """Test review creation for tasks."""

    @pytest.mark.asyncio
    async def test_creates_review_with_correct_fields(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Creating a review for a task should populate all fields correctly."""
        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            plan_step_id=None,
            title="Task for Review",
            task_type=TaskType.once,
            assignee_id=user_ids["member1"],
            status=TaskStatus.submitted,
        )
        db_session.add(task)
        await db_session.flush()

        review = await create_review_for_task(
            db_session,
            task,
            family_id,
            evidence_text="I completed it",
            evidence_photos=["photo1.jpg", "photo2.jpg"],
        )

        assert review is not None
        assert review.family_id == family_id
        assert review.target_type == ReviewTargetType.task
        assert review.target_id == task.id
        assert review.reviewer_id == user_ids["admin"]
        assert review.submitter_id == user_ids["member1"]
        assert review.status == ReviewStatus.pending
        assert review.evidence_text == "I completed it"
        assert review.evidence_photos == ["photo1.jpg", "photo2.jpg"]

    @pytest.mark.asyncio
    async def test_returns_none_when_no_reviewer(self, db_session):
        """Should return None if no reviewer can be determined (no family members)."""
        orphan_family_id = uuid.uuid4()
        task = Task(
            id=uuid.uuid4(),
            family_id=orphan_family_id,
            plan_step_id=None,
            title="Orphan Task",
            task_type=TaskType.once,
            assignee_id=uuid.uuid4(),
            status=TaskStatus.submitted,
        )
        db_session.add(task)
        await db_session.flush()

        review = await create_review_for_task(db_session, task, orphan_family_id)
        assert review is None


class TestCreateReviewForAction:
    """Test review creation for actions."""

    @pytest.mark.asyncio
    async def test_creates_review_with_correct_fields(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Creating a review for an action should populate all fields correctly."""
        action = Action(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_ids["member2"],
            task_id=None,
            plan_step_id=None,
            title="Action for Review",
            action_type=ActionType.schedule,
            status=ActionStatus.submitted,
        )
        db_session.add(action)
        await db_session.flush()

        review = await create_review_for_action(
            db_session,
            action,
            family_id,
            evidence_text="Done!",
            evidence_qrcode="qr-code-data",
        )

        assert review is not None
        assert review.family_id == family_id
        assert review.target_type == ReviewTargetType.action
        assert review.target_id == action.id
        assert review.reviewer_id == user_ids["admin"]
        assert review.submitter_id == user_ids["member2"]
        assert review.status == ReviewStatus.pending
        assert review.evidence_text == "Done!"
        assert review.evidence_qrcode == "qr-code-data"


# ─── Review Approval/Rejection Tests ──────────────────────────────────────────


class TestApproveReview:
    """Test review approval logic."""

    @pytest.mark.asyncio
    async def test_approve_task_review_updates_task_status(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Approving a task review should set task status to approved."""
        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            plan_step_id=None,
            title="Task to Approve",
            task_type=TaskType.once,
            assignee_id=user_ids["member1"],
            status=TaskStatus.submitted,
        )
        db_session.add(task)
        await db_session.flush()

        review = await create_review_for_task(db_session, task, family_id)
        assert review is not None

        approved_review = await approve_review(db_session, review, comment="Good job!")

        assert approved_review.status == ReviewStatus.approved
        assert approved_review.comment == "Good job!"

        # Verify task status updated
        from sqlalchemy import select
        task_result = await db_session.execute(select(Task).where(Task.id == task.id))
        updated_task = task_result.scalar_one()
        assert updated_task.status == TaskStatus.approved

    @pytest.mark.asyncio
    async def test_approve_action_review_updates_action_status(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Approving an action review should set action status to approved."""
        action = Action(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_ids["member1"],
            task_id=None,
            plan_step_id=None,
            title="Action to Approve",
            action_type=ActionType.todo,
            status=ActionStatus.submitted,
        )
        db_session.add(action)
        await db_session.flush()

        review = await create_review_for_action(db_session, action, family_id)
        assert review is not None

        approved_review = await approve_review(db_session, review)

        assert approved_review.status == ReviewStatus.approved

        # Verify action status updated
        from sqlalchemy import select
        action_result = await db_session.execute(select(Action).where(Action.id == action.id))
        updated_action = action_result.scalar_one()
        assert updated_action.status == ActionStatus.approved


class TestRejectReview:
    """Test review rejection logic."""

    @pytest.mark.asyncio
    async def test_reject_task_review_reverts_task_status(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Rejecting a task review should revert task status to in_progress."""
        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            plan_step_id=None,
            title="Task to Reject",
            task_type=TaskType.once,
            assignee_id=user_ids["member1"],
            status=TaskStatus.submitted,
        )
        db_session.add(task)
        await db_session.flush()

        review = await create_review_for_task(db_session, task, family_id)
        assert review is not None

        rejected_review = await reject_review(db_session, review, comment="Needs more work")

        assert rejected_review.status == ReviewStatus.rejected
        assert rejected_review.comment == "Needs more work"

        # Verify task status reverted
        from sqlalchemy import select
        task_result = await db_session.execute(select(Task).where(Task.id == task.id))
        updated_task = task_result.scalar_one()
        assert updated_task.status == TaskStatus.in_progress

    @pytest.mark.asyncio
    async def test_reject_action_review_reverts_action_status(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Rejecting an action review should revert action status to in_progress."""
        action = Action(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_ids["member1"],
            task_id=None,
            plan_step_id=None,
            title="Action to Reject",
            action_type=ActionType.todo,
            status=ActionStatus.submitted,
        )
        db_session.add(action)
        await db_session.flush()

        review = await create_review_for_action(db_session, action, family_id)
        assert review is not None

        rejected_review = await reject_review(db_session, review, comment="Redo this")

        assert rejected_review.status == ReviewStatus.rejected

        # Verify action status reverted
        from sqlalchemy import select
        action_result = await db_session.execute(select(Action).where(Action.id == action.id))
        updated_action = action_result.scalar_one()
        assert updated_action.status == ActionStatus.in_progress


# ─── Query Tests ───────────────────────────────────────────────────────────────


class TestGetPendingReviews:
    """Test pending reviews query."""

    @pytest.mark.asyncio
    async def test_returns_only_pending_reviews_for_reviewer(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Should only return pending reviews assigned to the specified reviewer."""
        # Create two tasks and reviews
        task1 = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            plan_step_id=None,
            title="Task 1",
            task_type=TaskType.once,
            assignee_id=user_ids["member1"],
            status=TaskStatus.submitted,
        )
        task2 = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            plan_step_id=None,
            title="Task 2",
            task_type=TaskType.once,
            assignee_id=user_ids["member2"],
            status=TaskStatus.submitted,
        )
        db_session.add_all([task1, task2])
        await db_session.flush()

        review1 = await create_review_for_task(db_session, task1, family_id)
        review2 = await create_review_for_task(db_session, task2, family_id)

        # Approve one review
        await approve_review(db_session, review1)

        # Query pending reviews for admin
        reviews, total = await get_pending_reviews(
            db_session, family_id, user_ids["admin"]
        )

        assert total == 1
        assert len(reviews) == 1
        assert reviews[0].id == review2.id

    @pytest.mark.asyncio
    async def test_pagination_works(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Should respect page and page_size parameters."""
        # Create 3 tasks and reviews
        for i in range(3):
            task = Task(
                id=uuid.uuid4(),
                family_id=family_id,
                plan_step_id=None,
                title=f"Task {i}",
                task_type=TaskType.once,
                assignee_id=user_ids["member1"],
                status=TaskStatus.submitted,
            )
            db_session.add(task)
            await db_session.flush()
            await create_review_for_task(db_session, task, family_id)

        # Get page 1 with page_size=2
        reviews, total = await get_pending_reviews(
            db_session, family_id, user_ids["admin"], page=1, page_size=2
        )
        assert total == 3
        assert len(reviews) == 2

        # Get page 2
        reviews, total = await get_pending_reviews(
            db_session, family_id, user_ids["admin"], page=2, page_size=2
        )
        assert total == 3
        assert len(reviews) == 1


class TestGetReviewById:
    """Test getting a review by ID."""

    @pytest.mark.asyncio
    async def test_returns_review_when_found(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Should return the review when it exists in the family."""
        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            plan_step_id=None,
            title="Task",
            task_type=TaskType.once,
            assignee_id=user_ids["member1"],
            status=TaskStatus.submitted,
        )
        db_session.add(task)
        await db_session.flush()

        review = await create_review_for_task(db_session, task, family_id)
        assert review is not None

        found = await get_review_by_id(db_session, review.id, family_id)
        assert found is not None
        assert found.id == review.id

    @pytest.mark.asyncio
    async def test_returns_none_for_wrong_family(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Should return None when review belongs to a different family."""
        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            plan_step_id=None,
            title="Task",
            task_type=TaskType.once,
            assignee_id=user_ids["member1"],
            status=TaskStatus.submitted,
        )
        db_session.add(task)
        await db_session.flush()

        review = await create_review_for_task(db_session, task, family_id)
        assert review is not None

        # Try to find with a different family_id
        other_family_id = uuid.uuid4()
        found = await get_review_by_id(db_session, review.id, other_family_id)
        assert found is None
