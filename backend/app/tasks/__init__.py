"""Celery application configuration.

Creates and configures the Celery app instance with Redis as broker
and result backend. The app is importable as:

    from app.tasks import celery_app
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Create Celery application instance
celery_app = Celery("ai_family_butler")

# Configure Celery
celery_app.conf.update(
    # Broker and result backend
    broker_url=settings.CELERY_BROKER_URL,
    result_backend=settings.CELERY_RESULT_BACKEND,
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Timezone
    timezone="Asia/Shanghai",
    enable_utc=True,
    # Task tracking and reliability
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # In debug mode, execute tasks eagerly (synchronously, no broker needed)
    task_always_eager=settings.DEBUG,
    task_eager_propagates=settings.DEBUG,
    # Beat schedule for periodic tasks
    beat_schedule={
        "task-timeout-penalty": {
            "task": "app.tasks.ai_tasks.check_task_timeout_penalty",
            "schedule": crontab(minute="*/10"),  # Every 10 minutes
        },
        "recurring-task-generation": {
            "task": "app.tasks.ai_tasks.generate_recurring_tasks",
            "schedule": crontab(hour=0, minute=0),  # Daily at midnight
        },
        "plan-overdue-check": {
            "task": "app.tasks.ai_tasks.check_plan_overdue",
            "schedule": crontab(minute=0),  # Every hour
        },
    },
)

# Auto-discover task modules
celery_app.autodiscover_tasks(["app.tasks"])
