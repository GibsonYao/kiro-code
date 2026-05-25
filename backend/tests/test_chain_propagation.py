"""Tests for chain propagation and points services.

Tests cover:
- Points service: get_or_create_account, award_points, deduct_points
- Chain propagation: task approval, action approval, plan progress, goal progress
- Integration with review approval flow
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base
from app.models.action import Action, ActionStatus, ActionType
from app.models.family import Family, FamilyMember, FamilyRole
from app.models.goal import Goal, GoalStatus
from app.models.plan import Plan, PlanStatus, PlanStep, PlanStepStatus, StepType
from app.models.points import PointsAccount, PointsTransaction, PointsTransactionType
from app.models.review import Review, ReviewStatus, ReviewTargetType
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.services.chain_propagation_service import (
    propagate_action_approval,
    propagate_task_approval,
    update_goal_progress,
    update_plan_progress,
)
from app.services.points_service import award_points, deduct_points, get_or_create_account
from app.services.review_service import approve_review


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
    for key, uid in user_ids.items():
        user = User(id=uid, nickname=key)
        db_session.add(user)

    family = Family(
        id=family_id,
        name="Test Family",
        invite_code="CHAIN123",
        created_by=user_ids["admin"],
    )
    db_session.add(family)

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


# ─── Points Service Tests ──────────────────────────────────────────────────────


class TestGetOrCreateAccount:
    """Test get_or_create_account function."""

    @pytest.mark.asyncio
    async def test_creates_new_account(self, db_session, user_ids, family_id, setup_family):
        """Should create a new account when none exists."""
        account = await get_or_create_account(db_session, family_id, user_ids["member1"])

        assert account is not None
        assert account.family_id == family_id
        assert account.user_id == user_ids["member1"]
        assert account.balance == 0
        assert account.total_earned == 0
        assert account.total_spent == 0

    @pytest.mark.asyncio
    async def test_returns_existing_account(self, db_session, user_ids, family_id, setup_family):
        """Should return existing account without creating a duplicate."""
        account1 = await get_or_create_account(db_session, family_id, user_ids["member1"])
        account2 = await get_or_create_account(db_session, family_id, user_ids["member1"])

        assert account1.id == account2.id


class TestAwardPoints:
    """Test award_points function."""

    @pytest.mark.asyncio
    async def test_awards_points_and_creates_transaction(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Should increase balance, total_earned, and create a reward transaction."""
        source_id = uuid.uuid4()
        transaction = await award_points(
            db_session,
            family_id,
            user_ids["member1"],
            amount=50,
            source_type="task",
            source_id=source_id,
            description="Task reward",
        )

        assert transaction is not None
        assert transaction.type == PointsTransactionType.reward
        assert transaction.amount == 50
        assert transaction.balance_after == 50
        assert transaction.source_type == "task"
        assert transaction.source_id == source_id
        assert transaction.description == "Task reward"

        # Verify account updated
        account = await get_or_create_account(db_session, family_id, user_ids["member1"])
        assert account.balance == 50
        assert account.total_earned == 50

    @pytest.mark.asyncio
    async def test_cumulative_awards(self, db_session, user_ids, family_id, setup_family):
        """Multiple awards should accumulate correctly."""
        await award_points(
            db_session, family_id, user_ids["member1"],
            amount=30, source_type="task", source_id=uuid.uuid4(), description="First",
        )
        tx2 = await award_points(
            db_session, family_id, user_ids["member1"],
            amount=20, source_type="action", source_id=uuid.uuid4(), description="Second",
        )

        assert tx2.balance_after == 50

        account = await get_or_create_account(db_session, family_id, user_ids["member1"])
        assert account.balance == 50
        assert account.total_earned == 50


class TestDeductPoints:
    """Test deduct_points function."""

    @pytest.mark.asyncio
    async def test_deducts_points_and_creates_transaction(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Should decrease balance, increase total_spent, and create a penalty transaction."""
        # First award some points
        await award_points(
            db_session, family_id, user_ids["member1"],
            amount=100, source_type="task", source_id=uuid.uuid4(), description="Award",
        )

        source_id = uuid.uuid4()
        transaction = await deduct_points(
            db_session, family_id, user_ids["member1"],
            amount=30, source_type="task", source_id=source_id, description="Penalty",
        )

        assert transaction is not None
        assert transaction.type == PointsTransactionType.penalty
        assert transaction.amount == -30
        assert transaction.balance_after == 70

        account = await get_or_create_account(db_session, family_id, user_ids["member1"])
        assert account.balance == 70
        assert account.total_spent == 30

    @pytest.mark.asyncio
    async def test_allows_negative_balance(self, db_session, user_ids, family_id, setup_family):
        """Balance can go negative (design allows it)."""
        transaction = await deduct_points(
            db_session, family_id, user_ids["member1"],
            amount=50, source_type="task", source_id=uuid.uuid4(), description="Penalty",
        )

        assert transaction.balance_after == -50

        account = await get_or_create_account(db_session, family_id, user_ids["member1"])
        assert account.balance == -50


# ─── Chain Propagation Tests ───────────────────────────────────────────────────


class TestPropagateTaskApproval:
    """Test propagate_task_approval function."""

    @pytest.mark.asyncio
    async def test_awards_points_on_task_approval(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Approving a task should award reward_points to the assignee."""
        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            plan_step_id=None,
            title="Rewarded Task",
            task_type=TaskType.once,
            assignee_id=user_ids["member1"],
            reward_points=25,
            status=TaskStatus.approved,
        )
        db_session.add(task)
        await db_session.flush()

        await propagate_task_approval(db_session, task)

        account = await get_or_create_account(db_session, family_id, user_ids["member1"])
        assert account.balance == 25
        assert account.total_earned == 25

    @pytest.mark.asyncio
    async def test_no_points_when_reward_is_zero(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Should not create a transaction when reward_points is 0."""
        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            plan_step_id=None,
            title="No Reward Task",
            task_type=TaskType.once,
            assignee_id=user_ids["member1"],
            reward_points=0,
            status=TaskStatus.approved,
        )
        db_session.add(task)
        await db_session.flush()

        await propagate_task_approval(db_session, task)

        account = await get_or_create_account(db_session, family_id, user_ids["member1"])
        assert account.balance == 0

    @pytest.mark.asyncio
    async def test_updates_plan_step_to_completed(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Approving a task linked to a plan step should mark the step as completed."""
        plan = Plan(
            id=uuid.uuid4(),
            family_id=family_id,
            goal_id=None,
            title="Test Plan",
            owner_id=user_ids["plan_owner"],
            status=PlanStatus.active,
        )
        db_session.add(plan)

        plan_step = PlanStep(
            id=uuid.uuid4(),
            plan_id=plan.id,
            title="Step 1",
            step_type=StepType.task,
            status=PlanStepStatus.in_progress,
        )
        db_session.add(plan_step)

        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            plan_step_id=plan_step.id,
            title="Linked Task",
            task_type=TaskType.once,
            assignee_id=user_ids["member1"],
            reward_points=10,
            status=TaskStatus.approved,
        )
        db_session.add(task)
        await db_session.flush()

        await propagate_task_approval(db_session, task)

        # Verify plan step is completed
        from sqlalchemy import select
        step_result = await db_session.execute(
            select(PlanStep).where(PlanStep.id == plan_step.id)
        )
        updated_step = step_result.scalar_one()
        assert updated_step.status == PlanStepStatus.completed


class TestPropagateActionApproval:
    """Test propagate_action_approval function."""

    @pytest.mark.asyncio
    async def test_awards_points_on_action_approval(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Approving an action should award reward_points to the user."""
        action = Action(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_ids["member1"],
            task_id=None,
            plan_step_id=None,
            title="Rewarded Action",
            action_type=ActionType.todo,
            reward_points=15,
            status=ActionStatus.approved,
        )
        db_session.add(action)
        await db_session.flush()

        await propagate_action_approval(db_session, action)

        account = await get_or_create_account(db_session, family_id, user_ids["member1"])
        assert account.balance == 15
        assert account.total_earned == 15

    @pytest.mark.asyncio
    async def test_no_points_when_action_reward_is_zero(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Should not create a transaction when action reward_points is 0."""
        action = Action(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_ids["member1"],
            task_id=None,
            plan_step_id=None,
            title="No Reward Action",
            action_type=ActionType.todo,
            reward_points=0,
            status=ActionStatus.approved,
        )
        db_session.add(action)
        await db_session.flush()

        await propagate_action_approval(db_session, action)

        account = await get_or_create_account(db_session, family_id, user_ids["member1"])
        assert account.balance == 0


class TestUpdatePlanProgress:
    """Test update_plan_progress function."""

    @pytest.mark.asyncio
    async def test_marks_plan_completed_when_all_steps_done(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Plan should be marked completed when all steps are completed."""
        plan = Plan(
            id=uuid.uuid4(),
            family_id=family_id,
            goal_id=None,
            title="Test Plan",
            owner_id=user_ids["plan_owner"],
            status=PlanStatus.active,
        )
        db_session.add(plan)

        step1 = PlanStep(
            id=uuid.uuid4(),
            plan_id=plan.id,
            title="Step 1",
            step_type=StepType.task,
            status=PlanStepStatus.completed,
        )
        step2 = PlanStep(
            id=uuid.uuid4(),
            plan_id=plan.id,
            title="Step 2",
            step_type=StepType.task,
            status=PlanStepStatus.completed,
        )
        db_session.add_all([step1, step2])
        await db_session.flush()

        await update_plan_progress(db_session, step2)

        from sqlalchemy import select
        plan_result = await db_session.execute(select(Plan).where(Plan.id == plan.id))
        updated_plan = plan_result.scalar_one()
        assert updated_plan.status == PlanStatus.completed

    @pytest.mark.asyncio
    async def test_plan_not_completed_when_steps_remain(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Plan should stay active when some steps are not completed."""
        plan = Plan(
            id=uuid.uuid4(),
            family_id=family_id,
            goal_id=None,
            title="Test Plan",
            owner_id=user_ids["plan_owner"],
            status=PlanStatus.active,
        )
        db_session.add(plan)

        step1 = PlanStep(
            id=uuid.uuid4(),
            plan_id=plan.id,
            title="Step 1",
            step_type=StepType.task,
            status=PlanStepStatus.completed,
        )
        step2 = PlanStep(
            id=uuid.uuid4(),
            plan_id=plan.id,
            title="Step 2",
            step_type=StepType.task,
            status=PlanStepStatus.pending,
        )
        db_session.add_all([step1, step2])
        await db_session.flush()

        await update_plan_progress(db_session, step1)

        from sqlalchemy import select
        plan_result = await db_session.execute(select(Plan).where(Plan.id == plan.id))
        updated_plan = plan_result.scalar_one()
        assert updated_plan.status == PlanStatus.active


class TestUpdateGoalProgress:
    """Test update_goal_progress function."""

    @pytest.mark.asyncio
    async def test_goal_progress_calculated_from_plans(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Goal progress should be (completed plans / total plans) * 100."""
        goal = Goal(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_ids["goal_owner"],
            title="Test Goal",
            owner_id=user_ids["goal_owner"],
            progress=0,
        )
        db_session.add(goal)

        plan1 = Plan(
            id=uuid.uuid4(),
            family_id=family_id,
            goal_id=goal.id,
            title="Plan 1",
            owner_id=user_ids["plan_owner"],
            status=PlanStatus.completed,
        )
        plan2 = Plan(
            id=uuid.uuid4(),
            family_id=family_id,
            goal_id=goal.id,
            title="Plan 2",
            owner_id=user_ids["plan_owner"],
            status=PlanStatus.active,
        )
        db_session.add_all([plan1, plan2])
        await db_session.flush()

        await update_goal_progress(db_session, plan1)

        from sqlalchemy import select
        goal_result = await db_session.execute(select(Goal).where(Goal.id == goal.id))
        updated_goal = goal_result.scalar_one()
        assert updated_goal.progress == 50

    @pytest.mark.asyncio
    async def test_goal_completed_at_100_percent(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Goal should be marked completed when progress reaches 100%."""
        goal = Goal(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_ids["goal_owner"],
            title="Test Goal",
            owner_id=user_ids["goal_owner"],
            progress=0,
        )
        db_session.add(goal)

        plan = Plan(
            id=uuid.uuid4(),
            family_id=family_id,
            goal_id=goal.id,
            title="Only Plan",
            owner_id=user_ids["plan_owner"],
            status=PlanStatus.completed,
        )
        db_session.add(plan)
        await db_session.flush()

        await update_goal_progress(db_session, plan)

        from sqlalchemy import select
        goal_result = await db_session.execute(select(Goal).where(Goal.id == goal.id))
        updated_goal = goal_result.scalar_one()
        assert updated_goal.progress == 100
        assert updated_goal.status == GoalStatus.completed


# ─── Integration: Review Approval Triggers Chain Propagation ───────────────────


class TestApproveReviewChainPropagation:
    """Test that approve_review triggers chain propagation correctly."""

    @pytest.mark.asyncio
    async def test_approve_task_review_awards_points(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Approving a task review should award points via chain propagation."""
        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            plan_step_id=None,
            title="Task with Points",
            task_type=TaskType.once,
            assignee_id=user_ids["member1"],
            reward_points=40,
            status=TaskStatus.submitted,
        )
        db_session.add(task)
        await db_session.flush()

        review = Review(
            family_id=family_id,
            target_type=ReviewTargetType.task,
            target_id=task.id,
            reviewer_id=user_ids["admin"],
            submitter_id=user_ids["member1"],
            status=ReviewStatus.pending,
        )
        db_session.add(review)
        await db_session.flush()
        await db_session.refresh(review)

        await approve_review(db_session, review)

        # Verify points were awarded
        account = await get_or_create_account(db_session, family_id, user_ids["member1"])
        assert account.balance == 40
        assert account.total_earned == 40

    @pytest.mark.asyncio
    async def test_approve_task_review_propagates_plan_step(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Approving a task review should mark linked plan step as completed."""
        goal = Goal(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_ids["goal_owner"],
            title="Goal",
            owner_id=user_ids["goal_owner"],
            progress=0,
        )
        db_session.add(goal)

        plan = Plan(
            id=uuid.uuid4(),
            family_id=family_id,
            goal_id=goal.id,
            title="Plan",
            owner_id=user_ids["plan_owner"],
            status=PlanStatus.active,
        )
        db_session.add(plan)

        plan_step = PlanStep(
            id=uuid.uuid4(),
            plan_id=plan.id,
            title="Step 1",
            step_type=StepType.task,
            status=PlanStepStatus.in_progress,
        )
        db_session.add(plan_step)

        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            plan_step_id=plan_step.id,
            title="Linked Task",
            task_type=TaskType.once,
            assignee_id=user_ids["member1"],
            reward_points=10,
            status=TaskStatus.submitted,
        )
        db_session.add(task)
        await db_session.flush()

        review = Review(
            family_id=family_id,
            target_type=ReviewTargetType.task,
            target_id=task.id,
            reviewer_id=user_ids["admin"],
            submitter_id=user_ids["member1"],
            status=ReviewStatus.pending,
        )
        db_session.add(review)
        await db_session.flush()
        await db_session.refresh(review)

        await approve_review(db_session, review)

        # Verify plan step is completed
        from sqlalchemy import select
        step_result = await db_session.execute(
            select(PlanStep).where(PlanStep.id == plan_step.id)
        )
        updated_step = step_result.scalar_one()
        assert updated_step.status == PlanStepStatus.completed

        # Verify plan is completed (only one step)
        plan_result = await db_session.execute(select(Plan).where(Plan.id == plan.id))
        updated_plan = plan_result.scalar_one()
        assert updated_plan.status == PlanStatus.completed

        # Verify goal progress updated
        goal_result = await db_session.execute(select(Goal).where(Goal.id == goal.id))
        updated_goal = goal_result.scalar_one()
        assert updated_goal.progress == 100
        assert updated_goal.status == GoalStatus.completed

    @pytest.mark.asyncio
    async def test_approve_action_review_awards_points(
        self, db_session, user_ids, family_id, setup_family
    ):
        """Approving an action review should award points via chain propagation."""
        action = Action(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_ids["member2"],
            task_id=None,
            plan_step_id=None,
            title="Action with Points",
            action_type=ActionType.todo,
            reward_points=20,
            status=ActionStatus.submitted,
        )
        db_session.add(action)
        await db_session.flush()

        review = Review(
            family_id=family_id,
            target_type=ReviewTargetType.action,
            target_id=action.id,
            reviewer_id=user_ids["admin"],
            submitter_id=user_ids["member2"],
            status=ReviewStatus.pending,
        )
        db_session.add(review)
        await db_session.flush()
        await db_session.refresh(review)

        await approve_review(db_session, review)

        # Verify points were awarded
        account = await get_or_create_account(db_session, family_id, user_ids["member2"])
        assert account.balance == 20
        assert account.total_earned == 20
