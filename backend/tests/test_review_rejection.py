"""Tests for review rejection — status rollback and notification hook."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.action import Action, ActionStatus, ActionType
from app.models.base import Base
from app.models.family import Family, FamilyMember, FamilyRole
from app.models.review import Review, ReviewStatus, ReviewTargetType
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.services.review_service import (
    create_review_for_action,
    create_review_for_task,
    notify_rejection,
    reject_review,
)


# ─── Fixtures ──────────────────────────────────────────────────────────────────


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
    }


@pytest.fixture
def family_id():
    """Generate a fixed UUID for the test family."""
    return uuid.uuid4()


@pytest.fixture
async def setup_family(db_session: AsyncSession, user_ids, family_id):
    """Set up a family with admin and one member."""
    for key, uid in user_ids.items():
        user = User(id=uid, nickname=key)
        db_session.add(user)

    family = Family(
        id=family_id,
        name="Test Family",
        invite_code="REJECT01",
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

    member = FamilyMember(
        family_id=family_id,
        user_id=user_ids["member1"],
        role=FamilyRole.member,
        nickname_in_family="Member1",
    )
    db_session.add(member)

    await db_session.flush()
    return family


# ─── Rejection Status Rollback Tests ──────────────────────────────────────────


class TestRejectTaskReview:
    """Test that rejecting a task review reverts task status to in_progress."""

    @pytest.mark.asyncio
    async def test_reject_task_review_reverts_status(
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

        rejected_review = await reject_review(db_session, review, comment="Incomplete")

        assert rejected_review.status == ReviewStatus.rejected
        assert rejected_review.comment == "Incomplete"

        # Verify task status reverted to in_progress
        from sqlalchemy import select

        task_result = await db_session.execute(select(Task).where(Task.id == task.id))
        updated_task = task_result.scalar_one()
        assert updated_task.status == TaskStatus.in_progress


class TestRejectActionReview:
    """Test that rejecting an action review reverts action status to in_progress."""

    @pytest.mark.asyncio
    async def test_reject_action_review_reverts_status(
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

        rejected_review = await reject_review(db_session, review, comment="Try again")

        assert rejected_review.status == ReviewStatus.rejected

        # Verify action status reverted to in_progress
        from sqlalchemy import select

        action_result = await db_session.execute(
            select(Action).where(Action.id == action.id)
        )
        updated_action = action_result.scalar_one()
        assert updated_action.status == ActionStatus.in_progress


# ─── Notification Hook Tests ──────────────────────────────────────────────────


class TestNotifyRejection:
    """Test that notify_rejection is called during rejection."""

    @pytest.mark.asyncio
    async def test_notify_rejection_called_on_task_reject(
        self, db_session, user_ids, family_id, setup_family
    ):
        """notify_rejection should be called when a task review is rejected."""
        task = Task(
            id=uuid.uuid4(),
            family_id=family_id,
            plan_step_id=None,
            title="Task Notify Test",
            task_type=TaskType.once,
            assignee_id=user_ids["member1"],
            status=TaskStatus.submitted,
        )
        db_session.add(task)
        await db_session.flush()

        review = await create_review_for_task(db_session, task, family_id)
        assert review is not None

        with patch(
            "app.services.review_service.notify_rejection", new_callable=AsyncMock
        ) as mock_notify:
            await reject_review(db_session, review, comment="Not good enough")
            mock_notify.assert_called_once_with(db_session, review)

    @pytest.mark.asyncio
    async def test_notify_rejection_called_on_action_reject(
        self, db_session, user_ids, family_id, setup_family
    ):
        """notify_rejection should be called when an action review is rejected."""
        action = Action(
            id=uuid.uuid4(),
            family_id=family_id,
            user_id=user_ids["member1"],
            task_id=None,
            plan_step_id=None,
            title="Action Notify Test",
            action_type=ActionType.todo,
            status=ActionStatus.submitted,
        )
        db_session.add(action)
        await db_session.flush()

        review = await create_review_for_action(db_session, action, family_id)
        assert review is not None

        with patch(
            "app.services.review_service.notify_rejection", new_callable=AsyncMock
        ) as mock_notify:
            await reject_review(db_session, review, comment="Redo")
            mock_notify.assert_called_once_with(db_session, review)
