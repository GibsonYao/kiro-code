"""Tests for cascade unlink service.

Tests cover:
- check_downstream_links: Counting downstream items for each entity type
- unlink_downstream: Setting foreign keys to NULL for each entity type
- Edge cases: no downstream items, invalid entity types
"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.action import Action, ActionType
from app.models.base import Base
from app.models.family import Family, FamilyMember, FamilyRole
from app.models.goal import Goal, GoalStatus
from app.models.plan import Plan, PlanStatus, PlanStep, PlanStepStatus, StepType
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.models.wish import Wish, WishStatus
from app.services.cascade_unlink_service import (
    VALID_ENTITY_TYPES,
    check_downstream_links,
    unlink_downstream,
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
def family_id():
    """Generate a fixed UUID for the test family."""
    return uuid.uuid4()


@pytest.fixture
def user_id():
    """Generate a fixed UUID for the test user."""
    return uuid.uuid4()


@pytest.fixture
async def setup_base(db_session: AsyncSession, family_id, user_id):
    """Set up base user and family for tests."""
    user = User(id=user_id, nickname="TestUser")
    db_session.add(user)

    family = Family(
        id=family_id,
        name="Test Family",
        invite_code="UNLINK01",
        created_by=user_id,
    )
    db_session.add(family)

    member = FamilyMember(
        family_id=family_id,
        user_id=user_id,
        role=FamilyRole.admin,
        nickname_in_family="Admin",
    )
    db_session.add(member)

    await db_session.flush()
    return family


# ─── check_downstream_links Tests ─────────────────────────────────────────────


class TestCheckDownstreamLinksWish:
    """Test check_downstream_links for wish entity type."""

    @pytest.mark.asyncio
    async def test_wish_with_linked_goals(self, db_session, family_id, user_id, setup_base):
        """Should return count of goals linked to the wish."""
        wish = Wish(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_id,
            title="Test Wish",
            status=WishStatus.active,
        )
        db_session.add(wish)

        # Create 3 goals linked to this wish
        for i in range(3):
            goal = Goal(
                id=uuid.uuid4(),
                family_id=family_id,
                user_id=user_id,
                wish_id=wish.id,
                title=f"Goal {i}",
                owner_id=user_id,
            )
            db_session.add(goal)

        await db_session.flush()

        result = await check_downstream_links(db_session, "wish", wish.id)
        assert result == {"goals": 3}

    @pytest.mark.asyncio
    async def test_wish_with_no_linked_goals(self, db_session, family_id, user_id, setup_base):
        """Should return zero count when no goals are linked."""
        wish = Wish(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_id,
            title="Lonely Wish",
            status=WishStatus.active,
        )
        db_session.add(wish)
        await db_session.flush()

        result = await check_downstream_links(db_session, "wish", wish.id)
        assert result == {"goals": 0}


class TestCheckDownstreamLinksGoal:
    """Test check_downstream_links for goal entity type."""

    @pytest.mark.asyncio
    async def test_goal_with_linked_plans(self, db_session, family_id, user_id, setup_base):
        """Should return count of plans linked to the goal."""
        goal = Goal(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_id,
            title="Test Goal",
            owner_id=user_id,
        )
        db_session.add(goal)

        # Create 2 plans linked to this goal
        for i in range(2):
            plan = Plan(
                id=uuid.uuid4(),
                family_id=family_id,
                goal_id=goal.id,
                title=f"Plan {i}",
                owner_id=user_id,
                status=PlanStatus.active,
            )
            db_session.add(plan)

        await db_session.flush()

        result = await check_downstream_links(db_session, "goal", goal.id)
        assert result == {"plans": 2}

    @pytest.mark.asyncio
    async def test_goal_with_no_linked_plans(self, db_session, family_id, user_id, setup_base):
        """Should return zero count when no plans are linked."""
        goal = Goal(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_id,
            title="Lonely Goal",
            owner_id=user_id,
        )
        db_session.add(goal)
        await db_session.flush()

        result = await check_downstream_links(db_session, "goal", goal.id)
        assert result == {"plans": 0}


class TestCheckDownstreamLinksPlan:
    """Test check_downstream_links for plan entity type."""

    @pytest.mark.asyncio
    async def test_plan_with_linked_tasks_and_actions(
        self, db_session, family_id, user_id, setup_base
    ):
        """Should return counts of tasks and actions linked to plan steps."""
        plan = Plan(
            id=uuid.uuid4(),
            family_id=family_id,
            title="Test Plan",
            owner_id=user_id,
            status=PlanStatus.active,
        )
        db_session.add(plan)

        step1 = PlanStep(
            id=uuid.uuid4(),
            plan_id=plan.id,
            title="Step 1",
            step_type=StepType.task,
            status=PlanStepStatus.pending,
        )
        step2 = PlanStep(
            id=uuid.uuid4(),
            plan_id=plan.id,
            title="Step 2",
            step_type=StepType.action,
            status=PlanStepStatus.pending,
        )
        db_session.add_all([step1, step2])
        await db_session.flush()

        # Create 2 tasks linked to step1
        for i in range(2):
            task = Task(
                id=uuid.uuid4(),
                family_id=family_id,
                plan_step_id=step1.id,
                title=f"Task {i}",
                task_type=TaskType.once,
                status=TaskStatus.pending,
            )
            db_session.add(task)

        # Create 1 action linked to step2
        action = Action(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_id,
            plan_step_id=step2.id,
            title="Action 1",
            action_type=ActionType.todo,
        )
        db_session.add(action)
        await db_session.flush()

        result = await check_downstream_links(db_session, "plan", plan.id)
        assert result == {"tasks": 2, "actions": 1}

    @pytest.mark.asyncio
    async def test_plan_with_no_steps(self, db_session, family_id, user_id, setup_base):
        """Should return zero counts when plan has no steps."""
        plan = Plan(
            id=uuid.uuid4(),
            family_id=family_id,
            title="Empty Plan",
            owner_id=user_id,
            status=PlanStatus.draft,
        )
        db_session.add(plan)
        await db_session.flush()

        result = await check_downstream_links(db_session, "plan", plan.id)
        assert result == {"tasks": 0, "actions": 0}


class TestCheckDownstreamLinksTask:
    """Test check_downstream_links for task entity type."""

    @pytest.mark.asyncio
    async def test_task_with_linked_actions(self, db_session, family_id, user_id, setup_base):
        """Should return count of actions linked to the task."""
        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            title="Test Task",
            task_type=TaskType.once,
            status=TaskStatus.pending,
        )
        db_session.add(task)
        await db_session.flush()

        # Create 2 actions linked to this task
        for i in range(2):
            action = Action(
                id=uuid.uuid4(),
                family_id=family_id,
                user_id=user_id,
                task_id=task.id,
                title=f"Action {i}",
                action_type=ActionType.todo,
            )
            db_session.add(action)

        await db_session.flush()

        result = await check_downstream_links(db_session, "task", task.id)
        assert result == {"actions": 2}

    @pytest.mark.asyncio
    async def test_task_with_no_linked_actions(self, db_session, family_id, user_id, setup_base):
        """Should return zero count when no actions are linked."""
        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            title="Lonely Task",
            task_type=TaskType.once,
            status=TaskStatus.pending,
        )
        db_session.add(task)
        await db_session.flush()

        result = await check_downstream_links(db_session, "task", task.id)
        assert result == {"actions": 0}


class TestCheckDownstreamLinksInvalidType:
    """Test check_downstream_links with invalid entity type."""

    @pytest.mark.asyncio
    async def test_invalid_entity_type_raises_error(self, db_session, family_id, user_id, setup_base):
        """Should raise ValueError for invalid entity type."""
        with pytest.raises(ValueError, match="Invalid entity_type"):
            await check_downstream_links(db_session, "invalid", uuid.uuid4())


# ─── unlink_downstream Tests ──────────────────────────────────────────────────


class TestUnlinkDownstreamWish:
    """Test unlink_downstream for wish entity type."""

    @pytest.mark.asyncio
    async def test_unlinks_goals_from_wish(self, db_session, family_id, user_id, setup_base):
        """Should set goals.wish_id to NULL for all goals linked to the wish."""
        wish = Wish(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_id,
            title="Test Wish",
            status=WishStatus.active,
        )
        db_session.add(wish)

        goal1 = Goal(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_id,
            wish_id=wish.id,
            title="Goal 1",
            owner_id=user_id,
        )
        goal2 = Goal(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_id,
            wish_id=wish.id,
            title="Goal 2",
            owner_id=user_id,
        )
        db_session.add_all([goal1, goal2])
        await db_session.flush()

        await unlink_downstream(db_session, "wish", wish.id)

        # Verify goals are unlinked
        from sqlalchemy import select

        result = await db_session.execute(
            select(Goal).where(Goal.id.in_([goal1.id, goal2.id]))
        )
        goals = list(result.scalars().all())
        for goal in goals:
            assert goal.wish_id is None


class TestUnlinkDownstreamGoal:
    """Test unlink_downstream for goal entity type."""

    @pytest.mark.asyncio
    async def test_unlinks_plans_from_goal(self, db_session, family_id, user_id, setup_base):
        """Should set plans.goal_id to NULL for all plans linked to the goal."""
        goal = Goal(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_id,
            title="Test Goal",
            owner_id=user_id,
        )
        db_session.add(goal)

        plan1 = Plan(
            id=uuid.uuid4(),
            family_id=family_id,
            goal_id=goal.id,
            title="Plan 1",
            owner_id=user_id,
            status=PlanStatus.active,
        )
        plan2 = Plan(
            id=uuid.uuid4(),
            family_id=family_id,
            goal_id=goal.id,
            title="Plan 2",
            owner_id=user_id,
            status=PlanStatus.draft,
        )
        db_session.add_all([plan1, plan2])
        await db_session.flush()

        await unlink_downstream(db_session, "goal", goal.id)

        # Verify plans are unlinked
        from sqlalchemy import select

        result = await db_session.execute(
            select(Plan).where(Plan.id.in_([plan1.id, plan2.id]))
        )
        plans = list(result.scalars().all())
        for plan in plans:
            assert plan.goal_id is None


class TestUnlinkDownstreamPlan:
    """Test unlink_downstream for plan entity type."""

    @pytest.mark.asyncio
    async def test_unlinks_tasks_and_actions_from_plan_steps(
        self, db_session, family_id, user_id, setup_base
    ):
        """Should set tasks.plan_step_id and actions.plan_step_id to NULL."""
        plan = Plan(
            id=uuid.uuid4(),
            family_id=family_id,
            title="Test Plan",
            owner_id=user_id,
            status=PlanStatus.active,
        )
        db_session.add(plan)

        step = PlanStep(
            id=uuid.uuid4(),
            plan_id=plan.id,
            title="Step 1",
            step_type=StepType.task,
            status=PlanStepStatus.pending,
        )
        db_session.add(step)
        await db_session.flush()

        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            plan_step_id=step.id,
            title="Linked Task",
            task_type=TaskType.once,
            status=TaskStatus.pending,
        )
        action = Action(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_id,
            plan_step_id=step.id,
            title="Linked Action",
            action_type=ActionType.todo,
        )
        db_session.add_all([task, action])
        await db_session.flush()

        await unlink_downstream(db_session, "plan", plan.id)

        # Verify task is unlinked
        from sqlalchemy import select

        task_result = await db_session.execute(select(Task).where(Task.id == task.id))
        updated_task = task_result.scalar_one()
        assert updated_task.plan_step_id is None

        # Verify action is unlinked
        action_result = await db_session.execute(select(Action).where(Action.id == action.id))
        updated_action = action_result.scalar_one()
        assert updated_action.plan_step_id is None

    @pytest.mark.asyncio
    async def test_unlink_plan_with_no_steps_does_nothing(
        self, db_session, family_id, user_id, setup_base
    ):
        """Should not raise errors when plan has no steps."""
        plan = Plan(
            id=uuid.uuid4(),
            family_id=family_id,
            title="Empty Plan",
            owner_id=user_id,
            status=PlanStatus.draft,
        )
        db_session.add(plan)
        await db_session.flush()

        # Should not raise
        await unlink_downstream(db_session, "plan", plan.id)


class TestUnlinkDownstreamTask:
    """Test unlink_downstream for task entity type."""

    @pytest.mark.asyncio
    async def test_unlinks_actions_from_task(self, db_session, family_id, user_id, setup_base):
        """Should set actions.task_id to NULL for all actions linked to the task."""
        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            title="Test Task",
            task_type=TaskType.once,
            status=TaskStatus.pending,
        )
        db_session.add(task)
        await db_session.flush()

        action1 = Action(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_id,
            task_id=task.id,
            title="Action 1",
            action_type=ActionType.todo,
        )
        action2 = Action(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_id,
            task_id=task.id,
            title="Action 2",
            action_type=ActionType.schedule,
        )
        db_session.add_all([action1, action2])
        await db_session.flush()

        await unlink_downstream(db_session, "task", task.id)

        # Verify actions are unlinked
        from sqlalchemy import select

        result = await db_session.execute(
            select(Action).where(Action.id.in_([action1.id, action2.id]))
        )
        actions = list(result.scalars().all())
        for action in actions:
            assert action.task_id is None


class TestUnlinkDownstreamInvalidType:
    """Test unlink_downstream with invalid entity type."""

    @pytest.mark.asyncio
    async def test_invalid_entity_type_raises_error(self, db_session, family_id, user_id, setup_base):
        """Should raise ValueError for invalid entity type."""
        with pytest.raises(ValueError, match="Invalid entity_type"):
            await unlink_downstream(db_session, "invalid", uuid.uuid4())


# ─── Integration: Check then Unlink ───────────────────────────────────────────


class TestCheckThenUnlink:
    """Integration tests: check downstream links, then unlink them."""

    @pytest.mark.asyncio
    async def test_full_flow_wish(self, db_session, family_id, user_id, setup_base):
        """Full flow: check wish has downstream goals, unlink them, verify zero."""
        wish = Wish(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_id,
            title="Full Flow Wish",
            status=WishStatus.active,
        )
        db_session.add(wish)

        goal = Goal(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_id,
            wish_id=wish.id,
            title="Linked Goal",
            owner_id=user_id,
        )
        db_session.add(goal)
        await db_session.flush()

        # Check: should have 1 goal
        result = await check_downstream_links(db_session, "wish", wish.id)
        assert result == {"goals": 1}

        # Unlink
        await unlink_downstream(db_session, "wish", wish.id)

        # Check again: should have 0 goals
        result = await check_downstream_links(db_session, "wish", wish.id)
        assert result == {"goals": 0}

    @pytest.mark.asyncio
    async def test_full_flow_task(self, db_session, family_id, user_id, setup_base):
        """Full flow: check task has downstream actions, unlink them, verify zero."""
        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            title="Full Flow Task",
            task_type=TaskType.once,
            status=TaskStatus.pending,
        )
        db_session.add(task)

        action = Action(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_id,
            task_id=task.id,
            title="Linked Action",
            action_type=ActionType.todo,
        )
        db_session.add(action)
        await db_session.flush()

        # Check: should have 1 action
        result = await check_downstream_links(db_session, "task", task.id)
        assert result == {"actions": 1}

        # Unlink
        await unlink_downstream(db_session, "task", task.id)

        # Check again: should have 0 actions
        result = await check_downstream_links(db_session, "task", task.id)
        assert result == {"actions": 0}
