"""Tests for AI generation status query endpoint."""

from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def mock_async_result():
    """Create a mock Celery AsyncResult."""
    mock = MagicMock()
    mock.state = "PENDING"
    mock.result = None
    return mock


@pytest.mark.asyncio
class TestGetGenerationStatus:
    """Tests for GET /api/v1/ai/generation/{task_id}/status."""

    async def _get_status(self, task_id: str):
        """Helper to make a GET request to the status endpoint."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get(f"/api/v1/ai/generation/{task_id}/status")

    @patch("app.api.v1.endpoints.ai.celery_app")
    async def test_pending_task(self, mock_celery):
        """Test that PENDING state maps to 'pending' status."""
        mock_result = MagicMock()
        mock_result.state = "PENDING"
        mock_result.result = None
        mock_celery.AsyncResult.return_value = mock_result

        response = await self._get_status("test-task-123")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-123"
        assert data["status"] == "pending"
        assert data["result"] is None
        mock_celery.AsyncResult.assert_called_once_with("test-task-123")

    @patch("app.api.v1.endpoints.ai.celery_app")
    async def test_started_task(self, mock_celery):
        """Test that STARTED state maps to 'started' status."""
        mock_result = MagicMock()
        mock_result.state = "STARTED"
        mock_result.result = None
        mock_celery.AsyncResult.return_value = mock_result

        response = await self._get_status("task-456")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-456"
        assert data["status"] == "started"
        assert data["result"] is None

    @patch("app.api.v1.endpoints.ai.celery_app")
    async def test_completed_task(self, mock_celery):
        """Test that SUCCESS state maps to 'completed' with result."""
        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.result = {"display_text": "AI generated text", "status": "completed"}
        mock_celery.AsyncResult.return_value = mock_result

        response = await self._get_status("task-789")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-789"
        assert data["status"] == "completed"
        assert data["result"] == {"display_text": "AI generated text", "status": "completed"}

    @patch("app.api.v1.endpoints.ai.celery_app")
    async def test_failed_task(self, mock_celery):
        """Test that FAILURE state maps to 'failed' with error message."""
        mock_result = MagicMock()
        mock_result.state = "FAILURE"
        mock_result.result = RuntimeError("All providers failed")
        mock_celery.AsyncResult.return_value = mock_result

        response = await self._get_status("task-fail")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-fail"
        assert data["status"] == "failed"
        assert "All providers failed" in data["result"]

    @patch("app.api.v1.endpoints.ai.celery_app")
    async def test_retry_task(self, mock_celery):
        """Test that RETRY state maps to 'pending' status."""
        mock_result = MagicMock()
        mock_result.state = "RETRY"
        mock_result.result = None
        mock_celery.AsyncResult.return_value = mock_result

        response = await self._get_status("task-retry")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-retry"
        assert data["status"] == "pending"
        assert data["result"] is None

    @patch("app.api.v1.endpoints.ai.celery_app")
    async def test_unknown_state_defaults_to_pending(self, mock_celery):
        """Test that unknown Celery states default to 'pending'."""
        mock_result = MagicMock()
        mock_result.state = "REVOKED"
        mock_result.result = None
        mock_celery.AsyncResult.return_value = mock_result

        response = await self._get_status("task-revoked")

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-revoked"
        assert data["status"] == "pending"
