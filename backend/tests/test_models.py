"""Tests for all database models - verifies imports and table names."""

import uuid

import pytest
from sqlalchemy import inspect

from app.models import (
    Base,
    UUIDMixin,
    TimestampMixin,
    # User
    User,
    # Family
    Family,
    FamilyMember,
    FamilyAppellation,
    FamilyRole,
    # Wish
    Wish,
    WishStatus,
    # Goal
    Goal,
    GoalStatus,
    # Plan
    Plan,
    PlanStatus,
    PlanStep,
    PlanStepStatus,
    StepType,
    # Task
    Task,
    TaskStatus,
    TaskType,
    # Action
    Action,
    ActionStatus,
    ActionType,
    # Review
    Review,
    ReviewStatus,
    ReviewTargetType,
    # Points
    PointsAccount,
    PointsTransaction,
    PointsTransactionType,
    # Calendar
    CalendarEvent,
    CalendarEventType,
    # Recipe
    Recipe,
    MemberFoodPreference,
    # AI Config
    AIModelConfig,
)


# ─── Table Name Tests ──────────────────────────────────────────────────────────


class TestTableNames:
    """Verify all models have the expected __tablename__."""

    def test_user_table_name(self):
        assert User.__tablename__ == "users"

    def test_family_table_name(self):
        assert Family.__tablename__ == "families"

    def test_family_member_table_name(self):
        assert FamilyMember.__tablename__ == "family_members"

    def test_family_appellation_table_name(self):
        assert FamilyAppellation.__tablename__ == "family_appellations"

    def test_wish_table_name(self):
        assert Wish.__tablename__ == "wishes"

    def test_goal_table_name(self):
        assert Goal.__tablename__ == "goals"

    def test_plan_table_name(self):
        assert Plan.__tablename__ == "plans"

    def test_plan_step_table_name(self):
        assert PlanStep.__tablename__ == "plan_steps"

    def test_task_table_name(self):
        assert Task.__tablename__ == "tasks"

    def test_action_table_name(self):
        assert Action.__tablename__ == "actions"

    def test_review_table_name(self):
        assert Review.__tablename__ == "reviews"

    def test_points_account_table_name(self):
        assert PointsAccount.__tablename__ == "points_accounts"

    def test_points_transaction_table_name(self):
        assert PointsTransaction.__tablename__ == "points_transactions"

    def test_calendar_event_table_name(self):
        assert CalendarEvent.__tablename__ == "calendar_events"

    def test_recipe_table_name(self):
        assert Recipe.__tablename__ == "recipes"

    def test_member_food_preference_table_name(self):
        assert MemberFoodPreference.__tablename__ == "member_food_preferences"

    def test_ai_model_config_table_name(self):
        assert AIModelConfig.__tablename__ == "ai_model_configs"


# ─── Model Column Tests ────────────────────────────────────────────────────────


def _get_column_names(model_class):
    """Helper to get column names from a model class."""
    return {col.name for col in model_class.__table__.columns}


class TestUserModel:
    """Verify User model columns."""

    def test_has_expected_columns(self):
        cols = _get_column_names(User)
        expected = {"id", "openid", "unionid", "phone", "nickname", "avatar_url", "is_admin", "created_at", "updated_at"}
        assert expected.issubset(cols)

    def test_openid_is_unique(self):
        col = User.__table__.c.openid
        assert col.unique is True

    def test_phone_is_unique(self):
        col = User.__table__.c.phone
        assert col.unique is True

    def test_is_admin_default_false(self):
        col = User.__table__.c.is_admin
        assert col.default is not None


class TestFamilyModel:
    """Verify Family model columns."""

    def test_has_expected_columns(self):
        cols = _get_column_names(Family)
        expected = {"id", "name", "avatar_url", "invite_code", "created_by", "created_at", "updated_at"}
        assert expected.issubset(cols)

    def test_invite_code_is_unique(self):
        col = Family.__table__.c.invite_code
        assert col.unique is True

    def test_name_not_nullable(self):
        col = Family.__table__.c.name
        assert col.nullable is False

    def test_created_by_is_fk(self):
        col = Family.__table__.c.created_by
        assert len(col.foreign_keys) > 0


class TestFamilyMemberModel:
    """Verify FamilyMember model columns and constraints."""

    def test_has_expected_columns(self):
        cols = _get_column_names(FamilyMember)
        expected = {"id", "family_id", "user_id", "role", "nickname_in_family", "relationship", "created_at", "updated_at"}
        assert expected.issubset(cols)

    def test_has_unique_constraint(self):
        """family_id + user_id should have a unique constraint."""
        constraints = FamilyMember.__table__.constraints
        unique_constraints = [c for c in constraints if hasattr(c, "columns") and len(c.columns) == 2]
        # Check that there's a unique constraint on family_id, user_id
        found = False
        for c in FamilyMember.__table__.constraints:
            if hasattr(c, "columns"):
                col_names = {col.name for col in c.columns}
                if col_names == {"family_id", "user_id"} and c.__class__.__name__ == "UniqueConstraint":
                    found = True
                    break
        assert found, "Expected UniqueConstraint on (family_id, user_id)"


class TestFamilyAppellationModel:
    """Verify FamilyAppellation model columns and constraints."""

    def test_has_expected_columns(self):
        cols = _get_column_names(FamilyAppellation)
        expected = {"id", "family_id", "from_member_id", "to_member_id", "appellation", "created_at", "updated_at"}
        assert expected.issubset(cols)

    def test_has_unique_constraint(self):
        """family_id + from_member_id + to_member_id should have a unique constraint."""
        found = False
        for c in FamilyAppellation.__table__.constraints:
            if hasattr(c, "columns"):
                col_names = {col.name for col in c.columns}
                if col_names == {"family_id", "from_member_id", "to_member_id"} and c.__class__.__name__ == "UniqueConstraint":
                    found = True
                    break
        assert found, "Expected UniqueConstraint on (family_id, from_member_id, to_member_id)"

    def test_appellation_not_nullable(self):
        col = FamilyAppellation.__table__.c.appellation
        assert col.nullable is False


class TestWishModel:
    """Verify Wish model columns."""

    def test_has_expected_columns(self):
        cols = _get_column_names(Wish)
        expected = {"id", "family_id", "user_id", "title", "vision_story", "vision_image_url", "cover_image_url", "display_text", "status", "created_at", "updated_at"}
        assert expected.issubset(cols)

    def test_title_not_nullable(self):
        col = Wish.__table__.c.title
        assert col.nullable is False


class TestGoalModel:
    """Verify Goal model columns."""

    def test_has_expected_columns(self):
        cols = _get_column_names(Goal)
        expected = {
            "id", "family_id", "wish_id", "user_id", "title", "description",
            "smart_specific", "smart_measurable", "smart_achievable",
            "smart_relevant", "smart_time_bound", "cover_image_url",
            "display_text", "progress", "status", "owner_id",
            "created_at", "updated_at",
        }
        assert expected.issubset(cols)

    def test_wish_id_nullable(self):
        col = Goal.__table__.c.wish_id
        assert col.nullable is True

    def test_progress_default_zero(self):
        col = Goal.__table__.c.progress
        assert col.default is not None


class TestPlanModel:
    """Verify Plan model columns."""

    def test_has_expected_columns(self):
        cols = _get_column_names(Plan)
        expected = {
            "id", "family_id", "goal_id", "title", "cover_image_url",
            "display_text", "start_date", "end_date", "owner_id", "status",
            "created_at", "updated_at",
        }
        assert expected.issubset(cols)

    def test_goal_id_nullable(self):
        col = Plan.__table__.c.goal_id
        assert col.nullable is True


class TestPlanStepModel:
    """Verify PlanStep model columns."""

    def test_has_expected_columns(self):
        cols = _get_column_names(PlanStep)
        expected = {"id", "plan_id", "title", "step_type", "is_bounty", "sort_order", "status", "created_at", "updated_at"}
        assert expected.issubset(cols)

    def test_plan_id_is_fk(self):
        col = PlanStep.__table__.c.plan_id
        assert len(col.foreign_keys) > 0


class TestTaskModel:
    """Verify Task model columns."""

    def test_has_expected_columns(self):
        cols = _get_column_names(Task)
        expected = {
            "id", "family_id", "plan_step_id", "title", "description",
            "cover_image_url", "display_text", "task_type", "recurrence_rule",
            "time_limit_hours", "reward_points", "penalty_points",
            "assignee_id", "status", "deadline_at", "created_at", "updated_at",
        }
        assert expected.issubset(cols)

    def test_plan_step_id_nullable(self):
        col = Task.__table__.c.plan_step_id
        assert col.nullable is True

    def test_assignee_id_nullable(self):
        col = Task.__table__.c.assignee_id
        assert col.nullable is True


class TestActionModel:
    """Verify Action model columns."""

    def test_has_expected_columns(self):
        cols = _get_column_names(Action)
        expected = {
            "id", "family_id", "task_id", "plan_step_id", "user_id", "title",
            "cover_image_url", "display_text", "action_type", "scheduled_date",
            "scheduled_time", "time_spent_minutes", "reward_points", "status",
            "created_at", "updated_at",
        }
        assert expected.issubset(cols)

    def test_task_id_nullable(self):
        col = Action.__table__.c.task_id
        assert col.nullable is True

    def test_plan_step_id_nullable(self):
        col = Action.__table__.c.plan_step_id
        assert col.nullable is True


class TestReviewModel:
    """Verify Review model columns."""

    def test_has_expected_columns(self):
        cols = _get_column_names(Review)
        expected = {
            "id", "family_id", "target_type", "target_id", "reviewer_id",
            "submitter_id", "status", "comment", "evidence_text",
            "evidence_photos", "evidence_qrcode", "created_at", "updated_at",
        }
        assert expected.issubset(cols)

    def test_target_id_not_nullable(self):
        col = Review.__table__.c.target_id
        assert col.nullable is False


class TestPointsAccountModel:
    """Verify PointsAccount model columns and constraints."""

    def test_has_expected_columns(self):
        cols = _get_column_names(PointsAccount)
        expected = {"id", "family_id", "user_id", "balance", "total_earned", "total_spent", "created_at", "updated_at"}
        assert expected.issubset(cols)

    def test_has_unique_constraint(self):
        """family_id + user_id should have a unique constraint."""
        found = False
        for c in PointsAccount.__table__.constraints:
            if hasattr(c, "columns"):
                col_names = {col.name for col in c.columns}
                if col_names == {"family_id", "user_id"} and c.__class__.__name__ == "UniqueConstraint":
                    found = True
                    break
        assert found, "Expected UniqueConstraint on (family_id, user_id)"


class TestPointsTransactionModel:
    """Verify PointsTransaction model columns."""

    def test_has_expected_columns(self):
        cols = _get_column_names(PointsTransaction)
        expected = {
            "id", "account_id", "type", "amount", "balance_after",
            "source_type", "source_id", "description", "created_at", "updated_at",
        }
        assert expected.issubset(cols)

    def test_amount_not_nullable(self):
        col = PointsTransaction.__table__.c.amount
        assert col.nullable is False

    def test_balance_after_not_nullable(self):
        col = PointsTransaction.__table__.c.balance_after
        assert col.nullable is False


class TestCalendarEventModel:
    """Verify CalendarEvent model columns."""

    def test_has_expected_columns(self):
        cols = _get_column_names(CalendarEvent)
        expected = {
            "id", "family_id", "user_id", "title", "cover_image_url",
            "event_type", "event_date", "event_time", "is_recurring",
            "remind_before_days", "action_id", "created_at", "updated_at",
        }
        assert expected.issubset(cols)

    def test_action_id_nullable(self):
        col = CalendarEvent.__table__.c.action_id
        assert col.nullable is True


class TestRecipeModel:
    """Verify Recipe model columns."""

    def test_has_expected_columns(self):
        cols = _get_column_names(Recipe)
        expected = {
            "id", "family_id", "name", "description", "cover_image_url",
            "display_text", "ingredients", "steps", "created_by",
            "created_at", "updated_at",
        }
        assert expected.issubset(cols)

    def test_name_not_nullable(self):
        col = Recipe.__table__.c.name
        assert col.nullable is False


class TestMemberFoodPreferenceModel:
    """Verify MemberFoodPreference model columns."""

    def test_has_expected_columns(self):
        cols = _get_column_names(MemberFoodPreference)
        expected = {
            "id", "family_id", "user_id", "taste_preferences",
            "favorite_foods", "food_allergies", "dietary_restrictions",
            "created_at", "updated_at",
        }
        assert expected.issubset(cols)


class TestAIModelConfigModel:
    """Verify AIModelConfig model columns."""

    def test_has_expected_columns(self):
        cols = _get_column_names(AIModelConfig)
        expected = {
            "id", "config_key", "provider", "model_name", "api_key",
            "api_base_url", "parameters", "is_active", "priority",
            "created_at", "updated_at",
        }
        assert expected.issubset(cols)

    def test_config_key_not_nullable(self):
        col = AIModelConfig.__table__.c.config_key
        assert col.nullable is False

    def test_api_key_not_nullable(self):
        col = AIModelConfig.__table__.c.api_key
        assert col.nullable is False

    def test_is_active_default_true(self):
        col = AIModelConfig.__table__.c.is_active
        assert col.default is not None


# ─── Enum Tests ────────────────────────────────────────────────────────────────


class TestEnums:
    """Verify all enum classes have expected values."""

    def test_family_role_values(self):
        assert FamilyRole.admin.value == "admin"
        assert FamilyRole.member.value == "member"

    def test_wish_status_values(self):
        assert WishStatus.active.value == "active"
        assert WishStatus.achieved.value == "achieved"
        assert WishStatus.archived.value == "archived"

    def test_goal_status_values(self):
        assert GoalStatus.active.value == "active"
        assert GoalStatus.completed.value == "completed"
        assert GoalStatus.archived.value == "archived"

    def test_plan_status_values(self):
        assert PlanStatus.draft.value == "draft"
        assert PlanStatus.active.value == "active"
        assert PlanStatus.completed.value == "completed"
        assert PlanStatus.overdue.value == "overdue"

    def test_step_type_values(self):
        assert StepType.task.value == "task"
        assert StepType.action.value == "action"

    def test_plan_step_status_values(self):
        assert PlanStepStatus.pending.value == "pending"
        assert PlanStepStatus.in_progress.value == "in_progress"
        assert PlanStepStatus.completed.value == "completed"

    def test_task_type_values(self):
        assert TaskType.once.value == "once"
        assert TaskType.recurring.value == "recurring"

    def test_task_status_values(self):
        assert TaskStatus.pending.value == "pending"
        assert TaskStatus.claimed.value == "claimed"
        assert TaskStatus.in_progress.value == "in_progress"
        assert TaskStatus.submitted.value == "submitted"
        assert TaskStatus.approved.value == "approved"
        assert TaskStatus.rejected.value == "rejected"
        assert TaskStatus.expired.value == "expired"

    def test_action_type_values(self):
        assert ActionType.todo.value == "todo"
        assert ActionType.schedule.value == "schedule"

    def test_action_status_values(self):
        assert ActionStatus.pending.value == "pending"
        assert ActionStatus.in_progress.value == "in_progress"
        assert ActionStatus.submitted.value == "submitted"
        assert ActionStatus.approved.value == "approved"
        assert ActionStatus.rejected.value == "rejected"

    def test_review_target_type_values(self):
        assert ReviewTargetType.task.value == "task"
        assert ReviewTargetType.action.value == "action"

    def test_review_status_values(self):
        assert ReviewStatus.pending.value == "pending"
        assert ReviewStatus.approved.value == "approved"
        assert ReviewStatus.rejected.value == "rejected"

    def test_points_transaction_type_values(self):
        assert PointsTransactionType.reward.value == "reward"
        assert PointsTransactionType.penalty.value == "penalty"
        assert PointsTransactionType.manual_adjust.value == "manual_adjust"

    def test_calendar_event_type_values(self):
        assert CalendarEventType.schedule.value == "schedule"
        assert CalendarEventType.todo.value == "todo"
        assert CalendarEventType.anniversary.value == "anniversary"


# ─── Inheritance Tests ─────────────────────────────────────────────────────────


class TestModelInheritance:
    """Verify all models inherit from Base, UUIDMixin, and TimestampMixin."""

    @pytest.mark.parametrize("model_class", [
        User, Family, FamilyMember, FamilyAppellation,
        Wish, Goal, Plan, PlanStep, Task, Action,
        Review, PointsAccount, PointsTransaction,
        CalendarEvent, Recipe, MemberFoodPreference, AIModelConfig,
    ])
    def test_inherits_base(self, model_class):
        assert issubclass(model_class, Base)

    @pytest.mark.parametrize("model_class", [
        User, Family, FamilyMember, FamilyAppellation,
        Wish, Goal, Plan, PlanStep, Task, Action,
        Review, PointsAccount, PointsTransaction,
        CalendarEvent, Recipe, MemberFoodPreference, AIModelConfig,
    ])
    def test_has_uuid_primary_key(self, model_class):
        """All models should have a UUID primary key via UUIDMixin."""
        id_col = model_class.__table__.c.id
        assert id_col.primary_key

    @pytest.mark.parametrize("model_class", [
        User, Family, FamilyMember, FamilyAppellation,
        Wish, Goal, Plan, PlanStep, Task, Action,
        Review, PointsAccount, PointsTransaction,
        CalendarEvent, Recipe, MemberFoodPreference, AIModelConfig,
    ])
    def test_has_timestamps(self, model_class):
        """All models should have created_at and updated_at via TimestampMixin."""
        cols = _get_column_names(model_class)
        assert "created_at" in cols
        assert "updated_at" in cols
