"""Tests for AI generation fallback utilities."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.utils.ai_fallback import (
    DEFAULT_PLACEHOLDER_IMAGE_URL,
    get_fallback_text,
    get_fallback_image,
    get_fallback_vision_story,
    handle_ai_generation_failure,
)


class TestGetFallbackText:
    """Tests for get_fallback_text."""

    def test_returns_original_text_unchanged(self):
        """Should return the original text as-is."""
        assert get_fallback_text("我的愿望是环游世界") == "我的愿望是环游世界"

    def test_handles_empty_string(self):
        """Should handle empty string input."""
        assert get_fallback_text("") == ""

    def test_preserves_whitespace_and_special_chars(self):
        """Should preserve all characters including whitespace."""
        text = "  Hello\n\tWorld!  "
        assert get_fallback_text(text) == text


class TestGetFallbackImage:
    """Tests for get_fallback_image."""

    def test_returns_placeholder_url(self):
        """Should return the default placeholder image URL."""
        result = get_fallback_image()
        assert result == DEFAULT_PLACEHOLDER_IMAGE_URL

    def test_placeholder_url_is_valid_https(self):
        """The placeholder URL should be a valid HTTPS URL."""
        assert DEFAULT_PLACEHOLDER_IMAGE_URL.startswith("https://")


class TestGetFallbackVisionStory:
    """Tests for get_fallback_vision_story."""

    def test_returns_formatted_fallback_with_title(self):
        """Should return a fallback vision story incorporating the title."""
        result = get_fallback_vision_story("环游世界")
        assert result == "愿望：环游世界"

    def test_includes_title_in_output(self):
        """Should include the original title in the fallback text."""
        title = "学会弹钢琴"
        result = get_fallback_vision_story(title)
        assert title in result

    def test_handles_empty_title(self):
        """Should handle empty title gracefully."""
        result = get_fallback_vision_story("")
        assert result == "愿望："


class TestHandleAiGenerationFailure:
    """Tests for handle_ai_generation_failure."""

    @pytest.mark.asyncio
    async def test_updates_entity_with_fallback_value(self):
        """Should execute an UPDATE statement with the fallback value."""
        mock_session = AsyncMock()

        await handle_ai_generation_failure(
            entity_type="wish",
            entity_id="test-uuid-123",
            field="cover_image_url",
            fallback_value=DEFAULT_PLACEHOLDER_IMAGE_URL,
            db_session=mock_session,
        )

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_for_unknown_entity_type(self):
        """Should raise ValueError for unrecognized entity types."""
        mock_session = AsyncMock()

        with pytest.raises(ValueError, match="Unknown entity type: 'unknown'"):
            await handle_ai_generation_failure(
                entity_type="unknown",
                entity_id="test-uuid",
                field="cover_image_url",
                fallback_value="https://example.com/placeholder.png",
                db_session=mock_session,
            )

        mock_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_supports_all_entity_types(self):
        """Should support wish, goal, plan, task, and action entity types."""
        for entity_type in ["wish", "goal", "plan", "task", "action"]:
            mock_session = AsyncMock()
            # Should not raise
            await handle_ai_generation_failure(
                entity_type=entity_type,
                entity_id="test-uuid",
                field="display_text",
                fallback_value="fallback text",
                db_session=mock_session,
            )
            mock_session.execute.assert_called_once()
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_updates_vision_story_field(self):
        """Should support updating the vision_story field for wishes."""
        mock_session = AsyncMock()

        await handle_ai_generation_failure(
            entity_type="wish",
            entity_id="wish-uuid-456",
            field="vision_story",
            fallback_value="愿望：环游世界",
            db_session=mock_session,
        )

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()


class TestTaskLevelFallbackIntegration:
    """Tests verifying that Celery tasks apply fallback on max retries exceeded."""

    @patch("app.tasks.ai_tasks._get_async_session")
    @patch("app.tasks.ai_tasks.asyncio.run")
    def test_generate_text_task_applies_fallback_on_max_retries(
        self, mock_asyncio_run, mock_get_session
    ):
        """generate_text_task should apply text fallback when max retries exceeded."""
        from app.tasks.ai_tasks import generate_text_task

        # Simulate the task failing with MaxRetriesExceededError
        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        # First asyncio.run call raises (the main _run), second succeeds (fallback)
        mock_asyncio_run.side_effect = [RuntimeError("All providers failed"), None]

        # Mock the bound task's self (request context)
        task = generate_text_task
        task.request.retries = 3
        task.max_retries = 3

        # Patch self.retry to raise MaxRetriesExceededError
        with patch.object(task, "retry", side_effect=task.MaxRetriesExceededError()):
            result = task(
                entity_type="goal",
                entity_id="goal-uuid-123",
                config_key="text_generation",
                prompt="为目标生成文案",
            )

        assert result["status"] == "failed"
        assert result["fallback_applied"] is True
        assert result["fallback_text"] == "为目标生成文案"

    @patch("app.tasks.ai_tasks._get_async_session")
    @patch("app.tasks.ai_tasks.asyncio.run")
    def test_generate_image_task_applies_fallback_on_max_retries(
        self, mock_asyncio_run, mock_get_session
    ):
        """generate_image_task should apply placeholder image when max retries exceeded."""
        from app.tasks.ai_tasks import generate_image_task

        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        # First asyncio.run call raises (the main _run), second succeeds (fallback)
        mock_asyncio_run.side_effect = [RuntimeError("All providers failed"), None]

        task = generate_image_task
        task.request.retries = 3
        task.max_retries = 3

        with patch.object(task, "retry", side_effect=task.MaxRetriesExceededError()):
            result = task(
                entity_type="wish",
                entity_id="wish-uuid-456",
                config_key="image_generation",
                prompt="生成愿望配图",
            )

        assert result["status"] == "failed"
        assert result["fallback_applied"] is True
        assert result["fallback_image_url"] == DEFAULT_PLACEHOLDER_IMAGE_URL

    @patch("app.tasks.ai_tasks._get_async_session")
    @patch("app.tasks.ai_tasks.asyncio.run")
    def test_generate_vision_story_task_applies_fallback_on_max_retries(
        self, mock_asyncio_run, mock_get_session
    ):
        """generate_vision_story_task should apply vision story fallback when max retries exceeded."""
        from app.tasks.ai_tasks import generate_vision_story_task

        mock_session = AsyncMock()
        mock_get_session.return_value = mock_session

        # First asyncio.run call raises (the main _run), second succeeds (fallback)
        mock_asyncio_run.side_effect = [RuntimeError("All providers failed"), None]

        task = generate_vision_story_task
        task.request.retries = 3
        task.max_retries = 3

        with patch.object(task, "retry", side_effect=task.MaxRetriesExceededError()):
            result = task(
                wish_id="wish-uuid-789",
                title="环游世界",
            )

        assert result["status"] == "failed"
        assert result["fallback_applied"] is True
        assert result["fallback_vision_story"] == "愿望：环游世界"
