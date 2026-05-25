"""Tests for AI generation Celery tasks."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.tasks.ai_tasks import (
    _get_model_class,
    generate_image_task,
    generate_text_task,
    generate_vision_story_task,
)


class TestGetModelClass:
    """Tests for _get_model_class helper."""

    def test_wish_mapping(self):
        from app.models.wish import Wish
        assert _get_model_class("wish") is Wish

    def test_goal_mapping(self):
        from app.models.goal import Goal
        assert _get_model_class("goal") is Goal

    def test_plan_mapping(self):
        from app.models.plan import Plan
        assert _get_model_class("plan") is Plan

    def test_task_mapping(self):
        from app.models.task import Task
        assert _get_model_class("task") is Task

    def test_action_mapping(self):
        from app.models.action import Action
        assert _get_model_class("action") is Action

    def test_unknown_entity_type_raises(self):
        with pytest.raises(ValueError, match="Unknown entity_type"):
            _get_model_class("unknown")


class TestGenerateTextTask:
    """Tests for generate_text_task Celery task."""

    @patch("app.tasks.ai_tasks._get_async_session")
    @patch("app.services.ai_service.ai_adapter.generate_text", new_callable=AsyncMock)
    def test_generate_text_task_entity_not_found(self, mock_generate_text, mock_get_session):
        """Test that task returns error when entity is not found."""
        # Setup mock session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.close = AsyncMock()
        mock_get_session.return_value = mock_session

        mock_generate_text.return_value = "Generated text"

        entity_id = str(uuid.uuid4())
        result = generate_text_task(
            entity_type="wish",
            entity_id=entity_id,
            config_key="text_generation",
            prompt="Test prompt",
        )

        assert result["status"] == "error"
        assert result["error"] == "Entity not found"

    @patch("app.tasks.ai_tasks._get_async_session")
    @patch("app.services.ai_service.ai_adapter.generate_text", new_callable=AsyncMock)
    def test_generate_text_task_success(self, mock_generate_text, mock_get_session):
        """Test successful text generation and entity update."""
        # Setup mock entity
        mock_entity = MagicMock()
        mock_entity.display_text = None

        # Setup mock session
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_entity
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()
        mock_get_session.return_value = mock_session

        mock_generate_text.return_value = "AI generated display text"

        entity_id = str(uuid.uuid4())
        result = generate_text_task(
            entity_type="goal",
            entity_id=entity_id,
            config_key="text_generation",
            prompt="Generate text for goal",
        )

        assert result["status"] == "completed"
        assert result["display_text"] == "AI generated display text"
        assert mock_entity.display_text == "AI generated display text"
        mock_session.commit.assert_awaited_once()


class TestGenerateImageTask:
    """Tests for generate_image_task Celery task."""

    @patch("app.tasks.ai_tasks._get_async_session")
    @patch("app.services.ai_service.ai_adapter.generate_image", new_callable=AsyncMock)
    def test_generate_image_task_entity_not_found(self, mock_generate_image, mock_get_session):
        """Test that task returns error when entity is not found."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.close = AsyncMock()
        mock_get_session.return_value = mock_session

        mock_generate_image.return_value = "https://example.com/image.png"

        entity_id = str(uuid.uuid4())
        result = generate_image_task(
            entity_type="plan",
            entity_id=entity_id,
            config_key="image_generation",
            prompt="Test image prompt",
        )

        assert result["status"] == "error"
        assert result["error"] == "Entity not found"

    @patch("app.tasks.ai_tasks._get_async_session")
    @patch("app.services.ai_service.ai_adapter.generate_image", new_callable=AsyncMock)
    def test_generate_image_task_success(self, mock_generate_image, mock_get_session):
        """Test successful image generation and entity update."""
        mock_entity = MagicMock()
        mock_entity.cover_image_url = None

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_entity
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()
        mock_get_session.return_value = mock_session

        mock_generate_image.return_value = "https://oss.example.com/generated.png"

        entity_id = str(uuid.uuid4())
        result = generate_image_task(
            entity_type="task",
            entity_id=entity_id,
            config_key="image_generation",
            prompt="Generate cover image",
        )

        assert result["status"] == "completed"
        assert result["cover_image_url"] == "https://oss.example.com/generated.png"
        assert mock_entity.cover_image_url == "https://oss.example.com/generated.png"
        mock_session.commit.assert_awaited_once()


class TestGenerateVisionStoryTask:
    """Tests for generate_vision_story_task Celery task."""

    @patch("app.tasks.ai_tasks.generate_image_task")
    @patch("app.tasks.ai_tasks._generate_vision_image_task")
    @patch("app.tasks.ai_tasks._get_async_session")
    @patch("app.services.ai_service.ai_adapter.generate_text", new_callable=AsyncMock)
    def test_generate_vision_story_task_wish_not_found(
        self, mock_generate_text, mock_get_session, mock_vision_image, mock_image_task
    ):
        """Test that task returns error when wish is not found."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.close = AsyncMock()
        mock_get_session.return_value = mock_session

        mock_generate_text.return_value = "A beautiful vision story"

        wish_id = str(uuid.uuid4())
        result = generate_vision_story_task(
            wish_id=wish_id,
            title="学会弹钢琴",
        )

        assert result["status"] == "error"
        assert result["error"] == "Wish not found"

    @patch("app.tasks.ai_tasks._generate_vision_image_task")
    @patch("app.tasks.ai_tasks.generate_image_task")
    @patch("app.tasks.ai_tasks._get_async_session")
    @patch("app.services.ai_service.ai_adapter.generate_text", new_callable=AsyncMock)
    def test_generate_vision_story_task_success(
        self, mock_generate_text, mock_get_session, mock_image_task, mock_vision_image
    ):
        """Test successful vision story generation and image task trigger."""
        mock_wish = MagicMock()
        mock_wish.vision_story = None

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_wish
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.commit = AsyncMock()
        mock_session.close = AsyncMock()
        mock_get_session.return_value = mock_session

        mock_generate_text.return_value = "当钢琴的旋律在指尖流淌..."

        # Mock the delay calls
        mock_image_task.delay = MagicMock()
        mock_vision_image.delay = MagicMock()

        wish_id = str(uuid.uuid4())
        result = generate_vision_story_task(
            wish_id=wish_id,
            title="学会弹钢琴",
        )

        assert result["status"] == "completed"
        assert result["vision_story"] == "当钢琴的旋律在指尖流淌..."
        assert mock_wish.vision_story == "当钢琴的旋律在指尖流淌..."
        mock_session.commit.assert_awaited_once()

        # Verify image generation was triggered
        mock_image_task.delay.assert_called_once()
        call_kwargs = mock_image_task.delay.call_args[1]
        assert call_kwargs["entity_type"] == "wish"
        assert call_kwargs["entity_id"] == wish_id
        assert call_kwargs["config_key"] == "image_generation"


class TestGenerateTextTaskFailureHandling:
    """Tests for failure handling in generate_text_task."""

    @patch("app.tasks.ai_tasks._get_async_session")
    @patch("app.services.ai_service.ai_adapter.generate_text", new_callable=AsyncMock)
    def test_generate_text_task_ai_failure_raises_in_eager_mode(self, mock_generate_text, mock_get_session):
        """Test that AI adapter failure triggers retry (raises in eager mode).

        In eager mode (task_always_eager=True, task_eager_propagates=True),
        Celery retries propagate the exception. In production (non-eager),
        the task would retry up to max_retries and then return a failed dict.
        """
        mock_session = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()
        mock_get_session.return_value = mock_session

        mock_generate_text.side_effect = RuntimeError("All providers failed")

        entity_id = str(uuid.uuid4())
        # In eager mode, retry raises the original exception
        with pytest.raises(RuntimeError, match="All providers failed"):
            generate_text_task(
                entity_type="wish",
                entity_id=entity_id,
                config_key="text_generation",
                prompt="Test prompt",
            )
