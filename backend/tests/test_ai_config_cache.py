"""Tests for AI configuration caching mechanism."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.cache import get_cached, invalidate_ai_config_cache, invalidate_cache, set_cached
from app.services.ai_service import AIServiceAdapter


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock()
    client.delete = AsyncMock()
    client.scan = AsyncMock(return_value=(0, []))
    return client


@pytest.fixture
def adapter():
    """Create an AIServiceAdapter instance."""
    return AIServiceAdapter()


@pytest.fixture
def sample_configs_data():
    """Sample config data as it would be stored in cache."""
    return [
        {
            "id": "uuid-1",
            "config_key": "text_generation",
            "provider": "deepseek",
            "model_name": "deepseek-chat",
            "api_key": "sk-test-key",
            "api_base_url": "https://api.deepseek.com/v1",
            "parameters": {"temperature": 0.7},
            "is_active": True,
            "priority": 0,
        },
        {
            "id": "uuid-2",
            "config_key": "text_generation",
            "provider": "openai",
            "model_name": "gpt-4",
            "api_key": "sk-openai-key",
            "api_base_url": "https://api.openai.com/v1",
            "parameters": None,
            "is_active": True,
            "priority": 1,
        },
    ]


class TestGetCached:
    """Tests for the get_cached helper function."""

    async def test_returns_none_when_key_not_found(self, mock_redis):
        """get_cached returns None when key does not exist in Redis."""
        mock_redis.get.return_value = None
        with patch("app.core.cache.get_redis_client", return_value=mock_redis):
            result = await get_cached("ai_config:text_generation")
        assert result is None

    async def test_returns_deserialized_data_on_hit(self, mock_redis, sample_configs_data):
        """get_cached returns deserialized JSON data when key exists."""
        mock_redis.get.return_value = json.dumps(sample_configs_data)
        with patch("app.core.cache.get_redis_client", return_value=mock_redis):
            result = await get_cached("ai_config:text_generation")
        assert result == sample_configs_data
        assert len(result) == 2

    async def test_returns_none_on_redis_error(self, mock_redis):
        """get_cached returns None gracefully when Redis raises an error."""
        mock_redis.get.side_effect = Exception("Connection refused")
        with patch("app.core.cache.get_redis_client", return_value=mock_redis):
            result = await get_cached("ai_config:text_generation")
        assert result is None


class TestSetCached:
    """Tests for the set_cached helper function."""

    async def test_sets_value_with_default_ttl(self, mock_redis):
        """set_cached stores JSON-serialized value with 300s TTL by default."""
        data = [{"key": "value"}]
        with patch("app.core.cache.get_redis_client", return_value=mock_redis):
            await set_cached("ai_config:text_generation", data)
        mock_redis.set.assert_called_once_with(
            "ai_config:text_generation", json.dumps(data), ex=300
        )

    async def test_sets_value_with_custom_ttl(self, mock_redis):
        """set_cached respects custom TTL parameter."""
        data = [{"key": "value"}]
        with patch("app.core.cache.get_redis_client", return_value=mock_redis):
            await set_cached("ai_config:text_generation", data, ttl=60)
        mock_redis.set.assert_called_once_with(
            "ai_config:text_generation", json.dumps(data), ex=60
        )

    async def test_handles_redis_error_gracefully(self, mock_redis):
        """set_cached does not raise when Redis fails."""
        mock_redis.set.side_effect = Exception("Connection refused")
        with patch("app.core.cache.get_redis_client", return_value=mock_redis):
            # Should not raise
            await set_cached("ai_config:text_generation", {"data": 1})


class TestInvalidateCache:
    """Tests for the invalidate_cache helper function."""

    async def test_deletes_matching_keys(self, mock_redis):
        """invalidate_cache scans and deletes keys matching the pattern."""
        mock_redis.scan.return_value = (0, ["ai_config:text_generation", "ai_config:image_generation"])
        with patch("app.core.cache.get_redis_client", return_value=mock_redis):
            await invalidate_cache("ai_config:*")
        mock_redis.delete.assert_called_once_with(
            "ai_config:text_generation", "ai_config:image_generation"
        )

    async def test_handles_no_matching_keys(self, mock_redis):
        """invalidate_cache does nothing when no keys match."""
        mock_redis.scan.return_value = (0, [])
        with patch("app.core.cache.get_redis_client", return_value=mock_redis):
            await invalidate_cache("ai_config:*")
        mock_redis.delete.assert_not_called()


class TestInvalidateAiConfigCache:
    """Tests for the invalidate_ai_config_cache function."""

    async def test_deletes_specific_config_key(self, mock_redis):
        """invalidate_ai_config_cache deletes the exact cache key."""
        with patch("app.core.cache.get_redis_client", return_value=mock_redis):
            await invalidate_ai_config_cache("text_generation")
        mock_redis.delete.assert_called_once_with("ai_config:text_generation")


class TestLoadConfigsWithCache:
    """Tests for AIServiceAdapter._load_configs with caching."""

    async def test_cache_hit_returns_cached_data_without_db_query(
        self, adapter, mock_redis, sample_configs_data
    ):
        """When cache has data, _load_configs returns it without querying DB."""
        mock_redis.get.return_value = json.dumps(sample_configs_data)
        mock_db = AsyncMock()

        with patch("app.core.cache.get_redis_client", return_value=mock_redis):
            with patch("app.services.ai_service.get_cached") as mock_get_cached:
                mock_get_cached.return_value = sample_configs_data
                configs = await adapter._load_configs("text_generation", mock_db)

        # DB should NOT be queried
        mock_db.execute.assert_not_called()
        # Should return reconstructed configs
        assert len(configs) == 2
        assert configs[0].provider == "deepseek"
        assert configs[0].model_name == "deepseek-chat"
        assert configs[1].provider == "openai"

    async def test_cache_miss_queries_db_and_populates_cache(self, adapter, mock_redis):
        """When cache is empty, _load_configs queries DB and stores result in cache."""
        # Create mock DB result
        mock_config = MagicMock()
        mock_config.id = "uuid-1"
        mock_config.config_key = "text_generation"
        mock_config.provider = "deepseek"
        mock_config.model_name = "deepseek-chat"
        mock_config.api_key = "sk-test"
        mock_config.api_base_url = "https://api.deepseek.com/v1"
        mock_config.parameters = {"temperature": 0.7}
        mock_config.is_active = True
        mock_config.priority = 0

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_config]
        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        with patch("app.services.ai_service.get_cached", return_value=None) as mock_get:
            with patch("app.services.ai_service.set_cached") as mock_set:
                configs = await adapter._load_configs("text_generation", mock_db)

        # DB should be queried
        mock_db.execute.assert_called_once()
        # Cache should be populated
        mock_set.assert_called_once()
        call_args = mock_set.call_args
        assert call_args[0][0] == "ai_config:text_generation"
        assert call_args[1]["ttl"] == 300 or call_args[0][2] == 300
        # Should return configs from DB
        assert len(configs) == 1
        assert configs[0].provider == "deepseek"

    async def test_cache_invalidation_removes_key(self, mock_redis):
        """invalidate_ai_config_cache removes the cached config."""
        with patch("app.core.cache.get_redis_client", return_value=mock_redis):
            await invalidate_ai_config_cache("text_generation")
        mock_redis.delete.assert_called_once_with("ai_config:text_generation")
