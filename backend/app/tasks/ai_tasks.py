"""Celery tasks for AI content generation and periodic scheduling."""

import asyncio
import logging
import uuid

from sqlalchemy import select

from app.tasks import celery_app

logger = logging.getLogger(__name__)


def _get_sync_session():
    """Create a synchronous database session for Celery tasks.

    Celery tasks run in a synchronous context, so we need a sync session.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, sessionmaker

    from app.core.config import settings

    # Convert async URL to sync URL
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite+aiosqlite"):
        db_url = db_url.replace("sqlite+aiosqlite", "sqlite")
    elif db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql+asyncpg", "postgresql+psycopg2")

    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def _get_async_session():
    """Create an async database session for use within asyncio.run() in Celery tasks."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.core.config import settings

    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return session_factory()


def _get_model_class(entity_type: str):
    """Map entity_type string to the corresponding SQLAlchemy model class.

    Args:
        entity_type: One of 'wish', 'goal', 'plan', 'task', 'action'.

    Returns:
        The model class.

    Raises:
        ValueError: If entity_type is not recognized.
    """
    from app.models.action import Action
    from app.models.goal import Goal
    from app.models.plan import Plan
    from app.models.task import Task
    from app.models.wish import Wish

    model_map = {
        "wish": Wish,
        "goal": Goal,
        "plan": Plan,
        "task": Task,
        "action": Action,
    }
    model_class = model_map.get(entity_type)
    if model_class is None:
        raise ValueError(f"Unknown entity_type: {entity_type}. Must be one of {list(model_map.keys())}")
    return model_class


# ─── AI Generation Tasks ──────────────────────────────────────────────────────


@celery_app.task(name="app.tasks.ai_tasks.generate_text_task", bind=True, max_retries=3)
def generate_text_task(self, entity_type: str, entity_id: str, config_key: str, prompt: str) -> dict:
    """Generate AI text content and update the entity's display_text field.

    Uses asyncio.run() to call the async AI adapter within the synchronous Celery task.

    Args:
        entity_type: The type of entity ('wish', 'goal', 'plan', 'task', 'action').
        entity_id: UUID string of the entity to update.
        config_key: AI model configuration key (e.g., 'text_generation').
        prompt: The text generation prompt.

    Returns:
        Dict with generation status and result.
    """

    async def _run():
        from app.services.ai_service import ai_adapter

        async_session = _get_async_session()
        try:
            model_class = _get_model_class(entity_type)

            # Generate text via AI adapter
            generated_text = await ai_adapter.generate_text(config_key, prompt, async_session)

            # Update entity's display_text field
            result = await async_session.execute(
                select(model_class).where(model_class.id == uuid.UUID(entity_id))
            )
            entity = result.scalar_one_or_none()

            if entity is None:
                return {"status": "error", "entity_type": entity_type, "entity_id": entity_id, "error": "Entity not found"}

            entity.display_text = generated_text
            await async_session.commit()

            logger.info(f"Successfully generated text for {entity_type}/{entity_id}")
            return {
                "status": "completed",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "display_text": generated_text,
            }
        except Exception as e:
            await async_session.rollback()
            raise e
        finally:
            await async_session.close()

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error(f"generate_text_task failed for {entity_type}/{entity_id}: {exc}")
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            logger.error(f"generate_text_task max retries exceeded for {entity_type}/{entity_id}")
            # Apply fallback: use original prompt text as display_text
            from app.utils.ai_fallback import get_fallback_text, handle_ai_generation_failure

            fallback_text = get_fallback_text(prompt)
            try:
                asyncio.run(
                    handle_ai_generation_failure(
                        entity_type=entity_type,
                        entity_id=entity_id,
                        field="display_text",
                        fallback_value=fallback_text,
                        db_session=_get_async_session(),
                    )
                )
                logger.info(
                    f"Applied text fallback for {entity_type}/{entity_id}: using original prompt"
                )
            except Exception as fallback_exc:
                logger.error(
                    f"Failed to apply text fallback for {entity_type}/{entity_id}: {fallback_exc}"
                )
            return {
                "status": "failed",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "error": str(exc),
                "fallback_applied": True,
                "fallback_text": fallback_text,
            }


@celery_app.task(name="app.tasks.ai_tasks.generate_image_task", bind=True, max_retries=3)
def generate_image_task(self, entity_type: str, entity_id: str, config_key: str, prompt: str) -> dict:
    """Generate AI image and update the entity's cover_image_url field.

    Uses asyncio.run() to call the async AI adapter within the synchronous Celery task.

    Args:
        entity_type: The type of entity ('wish', 'goal', 'plan', 'task', 'action').
        entity_id: UUID string of the entity to update.
        config_key: AI model configuration key (e.g., 'image_generation').
        prompt: The image generation prompt.

    Returns:
        Dict with generation status and result.
    """

    async def _run():
        from app.services.ai_service import ai_adapter

        async_session = _get_async_session()
        try:
            model_class = _get_model_class(entity_type)

            # Generate image via AI adapter
            image_url = await ai_adapter.generate_image(config_key, prompt, async_session)

            # Update entity's cover_image_url field
            result = await async_session.execute(
                select(model_class).where(model_class.id == uuid.UUID(entity_id))
            )
            entity = result.scalar_one_or_none()

            if entity is None:
                return {"status": "error", "entity_type": entity_type, "entity_id": entity_id, "error": "Entity not found"}

            entity.cover_image_url = image_url
            await async_session.commit()

            logger.info(f"Successfully generated image for {entity_type}/{entity_id}")
            return {
                "status": "completed",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "cover_image_url": image_url,
            }
        except Exception as e:
            await async_session.rollback()
            raise e
        finally:
            await async_session.close()

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error(f"generate_image_task failed for {entity_type}/{entity_id}: {exc}")
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            logger.error(f"generate_image_task max retries exceeded for {entity_type}/{entity_id}")
            # Apply fallback: use default placeholder image
            from app.utils.ai_fallback import get_fallback_image, handle_ai_generation_failure

            fallback_image = get_fallback_image()
            try:
                asyncio.run(
                    handle_ai_generation_failure(
                        entity_type=entity_type,
                        entity_id=entity_id,
                        field="cover_image_url",
                        fallback_value=fallback_image,
                        db_session=_get_async_session(),
                    )
                )
                logger.info(
                    f"Applied image fallback for {entity_type}/{entity_id}: using placeholder image"
                )
            except Exception as fallback_exc:
                logger.error(
                    f"Failed to apply image fallback for {entity_type}/{entity_id}: {fallback_exc}"
                )
            return {
                "status": "failed",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "error": str(exc),
                "fallback_applied": True,
                "fallback_image_url": fallback_image,
            }


@celery_app.task(name="app.tasks.ai_tasks.generate_vision_story_task", bind=True, max_retries=3)
def generate_vision_story_task(self, wish_id: str, title: str) -> dict:
    """Generate AI vision story and then trigger image generation for a wish.

    This task:
    1. Generates a vision story text using AI with config_key="vision_story"
    2. Updates the wish's vision_story field
    3. Triggers generate_image_task to generate the vision_image_url

    Args:
        wish_id: UUID string of the wish.
        title: The wish title used to construct the prompt.

    Returns:
        Dict with generation status and result.
    """

    async def _run():
        from app.models.wish import Wish
        from app.services.ai_service import ai_adapter

        async_session = _get_async_session()
        try:
            # Build prompt based on the wish title
            prompt = (
                f"请为以下愿望生成一段富有感染力的愿景故事，描述当这个愿望实现时的美好场景。"
                f"愿望标题：「{title}」。"
                f"要求：200字以内，语言温暖有画面感，能激励人为之努力。"
            )

            # Generate vision story text
            vision_story = await ai_adapter.generate_text("vision_story", prompt, async_session)

            # Update wish's vision_story field
            result = await async_session.execute(
                select(Wish).where(Wish.id == uuid.UUID(wish_id))
            )
            wish = result.scalar_one_or_none()

            if wish is None:
                return {"status": "error", "wish_id": wish_id, "error": "Wish not found"}

            wish.vision_story = vision_story
            await async_session.commit()

            logger.info(f"Successfully generated vision story for wish/{wish_id}")
            return {
                "status": "completed",
                "wish_id": wish_id,
                "vision_story": vision_story,
            }
        except Exception as e:
            await async_session.rollback()
            raise e
        finally:
            await async_session.close()

    try:
        result = asyncio.run(_run())

        # If story generation succeeded, trigger image generation for the vision image
        if result.get("status") == "completed":
            image_prompt = (
                f"为以下愿望生成一张梦幻风格的愿景配图。"
                f"愿望：「{title}」。"
                f"风格：温暖、梦幻、充满希望的插画风格。"
            )
            generate_image_task.delay(
                entity_type="wish",
                entity_id=wish_id,
                config_key="image_generation",
                prompt=image_prompt,
            )
            # Also update the vision_image_url field specifically
            _update_wish_vision_image(wish_id, image_prompt)

        return result
    except Exception as exc:
        logger.error(f"generate_vision_story_task failed for wish/{wish_id}: {exc}")
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            logger.error(f"generate_vision_story_task max retries exceeded for wish/{wish_id}")
            # Apply fallback: use default vision story based on title
            from app.utils.ai_fallback import get_fallback_vision_story, handle_ai_generation_failure

            fallback_story = get_fallback_vision_story(title)
            try:
                asyncio.run(
                    handle_ai_generation_failure(
                        entity_type="wish",
                        entity_id=wish_id,
                        field="vision_story",
                        fallback_value=fallback_story,
                        db_session=_get_async_session(),
                    )
                )
                logger.info(
                    f"Applied vision story fallback for wish/{wish_id}: using default message"
                )
            except Exception as fallback_exc:
                logger.error(
                    f"Failed to apply vision story fallback for wish/{wish_id}: {fallback_exc}"
                )
            return {
                "status": "failed",
                "wish_id": wish_id,
                "error": str(exc),
                "fallback_applied": True,
                "fallback_vision_story": fallback_story,
            }


def _update_wish_vision_image(wish_id: str, prompt: str) -> None:
    """Trigger a separate task to update the wish's vision_image_url field.

    This is separate from cover_image_url — the vision story has its own image.
    We use a dedicated sub-task for this.
    """
    _generate_vision_image_task.delay(wish_id=wish_id, prompt=prompt)


@celery_app.task(name="app.tasks.ai_tasks._generate_vision_image_task", bind=True, max_retries=3)
def _generate_vision_image_task(self, wish_id: str, prompt: str) -> dict:
    """Internal task: Generate vision image and update wish's vision_image_url.

    Args:
        wish_id: UUID string of the wish.
        prompt: The image generation prompt.

    Returns:
        Dict with generation status.
    """

    async def _run():
        from app.models.wish import Wish
        from app.services.ai_service import ai_adapter

        async_session = _get_async_session()
        try:
            # Generate image via AI adapter
            image_url = await ai_adapter.generate_image("image_generation", prompt, async_session)

            # Update wish's vision_image_url field
            result = await async_session.execute(
                select(Wish).where(Wish.id == uuid.UUID(wish_id))
            )
            wish = result.scalar_one_or_none()

            if wish is None:
                return {"status": "error", "wish_id": wish_id, "error": "Wish not found"}

            wish.vision_image_url = image_url
            await async_session.commit()

            logger.info(f"Successfully generated vision image for wish/{wish_id}")
            return {
                "status": "completed",
                "wish_id": wish_id,
                "vision_image_url": image_url,
            }
        except Exception as e:
            await async_session.rollback()
            raise e
        finally:
            await async_session.close()

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error(f"_generate_vision_image_task failed for wish/{wish_id}: {exc}")
        try:
            raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            logger.error(f"_generate_vision_image_task max retries exceeded for wish/{wish_id}")
            return {
                "status": "failed",
                "wish_id": wish_id,
                "error": str(exc),
            }


# ─── Legacy stub tasks (kept for backward compatibility with beat schedule) ───


@celery_app.task(name="app.tasks.ai_tasks.generate_vision_story", bind=True, max_retries=3)
def generate_vision_story(self, wish_id: str) -> dict:
    """Generate AI vision story and image for a wish (legacy task).

    This task:
    1. Loads the wish from the database
    2. Generates a vision story text based on the wish title
    3. Generates a vision image based on the story
    4. Updates the wish record with generated content

    Args:
        wish_id: UUID of the wish to generate content for.

    Returns:
        Dict with generation status and result URLs.
    """
    from app.models.wish import Wish

    session = _get_sync_session()
    try:
        # Load the wish
        wish = session.execute(
            select(Wish).where(Wish.id == uuid.UUID(wish_id))
        ).scalar_one_or_none()

        if wish is None:
            return {"status": "error", "wish_id": wish_id, "error": "Wish not found"}

        # Delegate to the new async task
        generate_vision_story_task.delay(wish_id=wish_id, title=wish.title)

        return {
            "status": "delegated",
            "wish_id": wish_id,
            "message": "Delegated to generate_vision_story_task",
        }

    except Exception as exc:
        session.rollback()
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    finally:
        session.close()


@celery_app.task(name="app.tasks.ai_tasks.generate_goal_smart", bind=True, max_retries=3)
def generate_goal_smart(self, goal_id: str) -> dict:
    """Generate AI SMART description and cover image for a goal.

    Args:
        goal_id: UUID of the goal to generate content for.

    Returns:
        Dict with generation status and results.
    """
    from app.models.goal import Goal

    session = _get_sync_session()
    try:
        # Load the goal
        goal = session.execute(
            select(Goal).where(Goal.id == uuid.UUID(goal_id))
        ).scalar_one_or_none()

        if goal is None:
            return {"status": "error", "goal_id": goal_id, "error": "Goal not found"}

        # Generate SMART descriptions using AI
        prompt = (
            f"请为以下目标生成SMART描述。目标标题：「{goal.title}」，"
            f"描述：「{goal.description or goal.title}」。"
            f"请分别生成Specific、Measurable、Achievable、Relevant、Time-bound五个维度的描述。"
        )

        # Use the new generate_text_task for display_text
        generate_text_task.delay(
            entity_type="goal",
            entity_id=goal_id,
            config_key="text_generation",
            prompt=f"请为目标「{goal.title}」生成一段简洁有力的展示文案，20字以内。",
        )

        # Use the new generate_image_task for cover image
        generate_image_task.delay(
            entity_type="goal",
            entity_id=goal_id,
            config_key="image_generation",
            prompt=f"为目标「{goal.title}」生成一张激励人心的配图，风格：现代、简洁、积极向上。",
        )

        return {
            "status": "delegated",
            "goal_id": goal_id,
            "message": "Delegated text and image generation to async tasks",
        }

    except Exception as exc:
        session.rollback()
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    finally:
        session.close()


@celery_app.task(name="app.tasks.ai_tasks.generate_text")
def generate_text(prompt: str, config_key: str = "text_generation") -> dict:
    """Generate AI text content (legacy simple interface).

    Args:
        prompt: The text generation prompt.
        config_key: AI model configuration key to use.

    Returns:
        Dict with generated text content.
    """

    async def _run():
        from app.services.ai_service import ai_adapter

        async_session = _get_async_session()
        try:
            result = await ai_adapter.generate_text(config_key, prompt, async_session)
            return {"status": "completed", "text": result}
        finally:
            await async_session.close()

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error(f"generate_text failed: {exc}")
        return {"status": "failed", "error": str(exc)}


@celery_app.task(name="app.tasks.ai_tasks.generate_image")
def generate_image(prompt: str, config_key: str = "image_generation") -> dict:
    """Generate AI image content (legacy simple interface).

    Args:
        prompt: The image generation prompt.
        config_key: AI model configuration key to use.

    Returns:
        Dict with generated image URL.
    """

    async def _run():
        from app.services.ai_service import ai_adapter

        async_session = _get_async_session()
        try:
            result = await ai_adapter.generate_image(config_key, prompt, async_session)
            return {"status": "completed", "image_url": result}
        finally:
            await async_session.close()

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error(f"generate_image failed: {exc}")
        return {"status": "failed", "error": str(exc)}


# ─── Periodic Tasks (Celery Beat) ─────────────────────────────────────────────


@celery_app.task(name="app.tasks.ai_tasks.check_task_timeout_penalty")
def check_task_timeout_penalty() -> dict:
    """Periodic task: Check for expired tasks and apply timeout penalties.

    Runs every 10 minutes via Celery Beat.
    Scans tasks past their deadline and deducts penalty points.

    Returns:
        Dict with count of penalized tasks.
    """
    from datetime import datetime, timezone

    from sqlalchemy import select

    from app.models.points import PointsAccount, PointsTransaction, PointsTransactionType
    from app.models.task import Task, TaskStatus

    session = _get_sync_session()
    try:
        now = datetime.now(timezone.utc)

        # Find tasks that are past deadline and still in claimable/in-progress states
        stmt = select(Task).where(
            Task.status.in_([TaskStatus.claimed, TaskStatus.in_progress]),
            Task.deadline_at.isnot(None),
            Task.deadline_at < now,
            Task.penalty_points > 0,
        )
        result = session.execute(stmt)
        expired_tasks = list(result.scalars().all())

        penalized_count = 0
        for task in expired_tasks:
            # Mark task as expired
            task.status = TaskStatus.expired

            # Deduct penalty points from assignee
            if task.assignee_id and task.penalty_points > 0:
                # Find or skip if no points account
                acct_stmt = select(PointsAccount).where(
                    PointsAccount.family_id == task.family_id,
                    PointsAccount.user_id == task.assignee_id,
                )
                acct_result = session.execute(acct_stmt)
                account = acct_result.scalar_one_or_none()

                if account:
                    # Deduct points (balance can go negative)
                    account.balance -= task.penalty_points
                    account.total_spent += task.penalty_points

                    # Record transaction
                    transaction = PointsTransaction(
                        account_id=account.id,
                        type=PointsTransactionType.penalty,
                        amount=-task.penalty_points,
                        balance_after=account.balance,
                        source_type="task",
                        source_id=task.id,
                        description=f"任务超时惩罚：{task.title}",
                    )
                    session.add(transaction)

            penalized_count += 1

        session.commit()

        return {"penalized_count": penalized_count}

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@celery_app.task(name="app.tasks.ai_tasks.generate_recurring_tasks")
def generate_recurring_tasks() -> dict:
    """Periodic task: Generate next-cycle instances for recurring tasks.

    Runs daily at midnight via Celery Beat.
    Scans completed/approved recurring tasks and creates next occurrences.

    Returns:
        Dict with count of generated tasks.
    """
    from sqlalchemy import select

    from app.models.task import Task, TaskStatus, TaskType

    session = _get_sync_session()
    try:
        # Find recurring tasks that have been approved (completed cycle)
        stmt = select(Task).where(
            Task.task_type == TaskType.recurring,
            Task.status == TaskStatus.approved,
            Task.recurrence_rule.isnot(None),
        )
        result = session.execute(stmt)
        completed_recurring = list(result.scalars().all())

        generated_count = 0
        for task in completed_recurring:
            # Create next cycle instance
            new_task = Task(
                family_id=task.family_id,
                plan_step_id=task.plan_step_id,
                title=task.title,
                description=task.description,
                cover_image_url=task.cover_image_url,
                display_text=task.display_text,
                task_type=TaskType.recurring,
                recurrence_rule=task.recurrence_rule,
                time_limit_hours=task.time_limit_hours,
                reward_points=task.reward_points,
                penalty_points=task.penalty_points,
                assignee_id=task.assignee_id,
                status=TaskStatus.pending,
            )
            session.add(new_task)
            generated_count += 1

        session.commit()

        return {"generated_count": generated_count}

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@celery_app.task(name="app.tasks.ai_tasks.check_plan_overdue")
def check_plan_overdue() -> dict:
    """Periodic task: Check for overdue plans and send notifications.

    Runs every hour via Celery Beat.
    Scans plans past their end_date that are still active.

    Returns:
        Dict with count of overdue plans found.
    """
    from datetime import date

    from sqlalchemy import select

    from app.models.plan import Plan, PlanStatus

    session = _get_sync_session()
    try:
        today = date.today()

        # Find active plans that are past their end_date
        stmt = select(Plan).where(
            Plan.status == PlanStatus.active,
            Plan.end_date.isnot(None),
            Plan.end_date < today,
        )
        result = session.execute(stmt)
        overdue_plans = list(result.scalars().all())

        overdue_count = 0
        for plan in overdue_plans:
            # Mark as overdue
            plan.status = PlanStatus.overdue
            overdue_count += 1

        session.commit()

        return {"overdue_count": overdue_count}

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@celery_app.task(name="app.tasks.ai_tasks.check_anniversary_reminders")
def check_anniversary_reminders() -> dict:
    """Periodic task: Check for upcoming anniversaries and send reminders.

    Runs daily at 8:00 AM via Celery Beat.
    Checks each family's anniversaries and sends reminders N days before.

    Returns:
        Dict with count of reminders sent.
    """
    from datetime import date, timedelta

    from sqlalchemy import select

    from app.models.calendar import CalendarEvent, CalendarEventType
    from app.models.family import Family

    session = _get_sync_session()
    try:
        today = date.today()

        # Get all anniversary events
        stmt = select(CalendarEvent).where(
            CalendarEvent.event_type == CalendarEventType.anniversary,
        )
        result = session.execute(stmt)
        anniversaries = list(result.scalars().all())

        reminder_count = 0
        for ann in anniversaries:
            if ann.event_date is None:
                continue
            if ann.remind_before_days <= 0:
                continue

            # Calculate this year's anniversary date
            try:
                this_year_date = ann.event_date.replace(year=today.year)
            except ValueError:
                # Handle Feb 29 in non-leap years
                this_year_date = ann.event_date.replace(year=today.year, day=28)

            # If already passed this year, check next year
            if this_year_date < today:
                try:
                    this_year_date = ann.event_date.replace(year=today.year + 1)
                except ValueError:
                    this_year_date = ann.event_date.replace(year=today.year + 1, day=28)

            # Check if we should remind today
            remind_date = this_year_date - timedelta(days=ann.remind_before_days)
            if remind_date == today:
                # TODO: Send notification to all family members
                # For now, just count it. Notification service will be implemented in Task 19.
                logger.info(
                    f"Anniversary reminder: '{ann.title}' in {ann.remind_before_days} days "
                    f"(family_id={ann.family_id})"
                )
                reminder_count += 1

        session.commit()
        return {"reminder_count": reminder_count}

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
