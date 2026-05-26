"""Tests for Celery application configuration."""

from celery.schedules import crontab

from app.tasks import celery_app
from app.core.config import settings


class TestCeleryConfig:
    """Verify Celery app is configured correctly."""

    def test_celery_app_exists(self):
        """Celery app instance should be importable."""
        assert celery_app is not None

    def test_celery_app_name(self):
        """Celery app should have the correct name."""
        assert celery_app.main == "ai_family_butler"

    def test_broker_url(self):
        """Broker URL should match settings."""
        assert celery_app.conf.broker_url == settings.CELERY_BROKER_URL

    def test_result_backend(self):
        """Result backend should match settings."""
        assert celery_app.conf.result_backend == settings.CELERY_RESULT_BACKEND

    def test_task_serializer(self):
        """Task serializer should be JSON."""
        assert celery_app.conf.task_serializer == "json"

    def test_result_serializer(self):
        """Result serializer should be JSON."""
        assert celery_app.conf.result_serializer == "json"

    def test_accept_content(self):
        """Accept content should only include JSON."""
        assert celery_app.conf.accept_content == ["json"]

    def test_timezone(self):
        """Timezone should be Asia/Shanghai."""
        assert celery_app.conf.timezone == "Asia/Shanghai"

    def test_enable_utc(self):
        """UTC should be enabled."""
        assert celery_app.conf.enable_utc is True

    def test_task_track_started(self):
        """Task tracking should be enabled."""
        assert celery_app.conf.task_track_started is True

    def test_task_acks_late(self):
        """Late acknowledgment should be enabled for reliability."""
        assert celery_app.conf.task_acks_late is True

    def test_worker_prefetch_multiplier(self):
        """Worker prefetch multiplier should be 1 for fair scheduling."""
        assert celery_app.conf.worker_prefetch_multiplier == 1


class TestCeleryBeatSchedule:
    """Verify Celery Beat schedule is configured correctly."""

    def test_beat_schedule_has_four_entries(self):
        """Beat schedule should have four periodic task entries."""
        assert len(celery_app.conf.beat_schedule) == 4

    def test_task_timeout_penalty_schedule(self):
        """Task timeout penalty should run every 10 minutes."""
        entry = celery_app.conf.beat_schedule["task-timeout-penalty"]
        assert entry["task"] == "app.tasks.ai_tasks.check_task_timeout_penalty"
        assert entry["schedule"] == crontab(minute="*/10")

    def test_recurring_task_generation_schedule(self):
        """Recurring task generation should run daily at midnight."""
        entry = celery_app.conf.beat_schedule["recurring-task-generation"]
        assert entry["task"] == "app.tasks.ai_tasks.generate_recurring_tasks"
        assert entry["schedule"] == crontab(hour=0, minute=0)

    def test_plan_overdue_check_schedule(self):
        """Plan overdue check should run every hour."""
        entry = celery_app.conf.beat_schedule["plan-overdue-check"]
        assert entry["task"] == "app.tasks.ai_tasks.check_plan_overdue"
        assert entry["schedule"] == crontab(minute=0)


class TestCeleryTaskDiscovery:
    """Verify task autodiscovery and registration."""

    def test_tasks_are_registered(self):
        """Placeholder tasks should be discoverable."""
        # Force task registration by importing the module
        import app.tasks.ai_tasks  # noqa: F401

        registered_tasks = celery_app.tasks.keys()
        assert "app.tasks.ai_tasks.generate_vision_story" in registered_tasks
        assert "app.tasks.ai_tasks.generate_text" in registered_tasks
        assert "app.tasks.ai_tasks.generate_image" in registered_tasks
        assert "app.tasks.ai_tasks.check_task_timeout_penalty" in registered_tasks
        assert "app.tasks.ai_tasks.generate_recurring_tasks" in registered_tasks
        assert "app.tasks.ai_tasks.check_plan_overdue" in registered_tasks
