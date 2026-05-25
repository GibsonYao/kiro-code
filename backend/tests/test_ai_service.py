"""Tests for AI service adapter: registration, factory, and fallback logic."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.ai_service import (
    AIProvider,
    AIServiceAdapter,
    DashScopeProvider,
    DeepSeekProvider,
    OpenAICompatibleProvider,
    StableDiffusionProvider,
    ai_adapter,
)


# ─── Test Helpers ──────────────────────────────────────────────────────────────


class MockSuccessProvider(AIProvider):
    """A mock provider that always succeeds."""

    async def generate_text(self, prompt: str, **kwargs) -> str:
        return f"generated: {prompt}"

    async def generate_image(self, prompt: str, **kwargs) -> str:
        return f"https://example.com/image/{prompt}"


class MockFailProvider(AIProvider):
    """A mock provider that always raises an exception."""

    async def generate_text(self, prompt: str, **kwargs) -> str:
        raise RuntimeError("Provider unavailable")

    async def generate_image(self, prompt: str, **kwargs) -> str:
        raise RuntimeError("Provider unavailable")


class MockFailThenSuccessProvider(AIProvider):
    """A mock provider that fails on first call, succeeds on second."""

    call_count = 0

    async def generate_text(self, prompt: str, **kwargs) -> str:
        MockFailThenSuccessProvider.call_count += 1
        if MockFailThenSuccessProvider.call_count == 1:
            raise RuntimeError("Temporary failure")
        return f"recovered: {prompt}"

    async def generate_image(self, prompt: str, **kwargs) -> str:
        MockFailThenSuccessProvider.call_count += 1
        if MockFailThenSuccessProvider.call_count == 1:
            raise RuntimeError("Temporary failure")
        return f"https://example.com/recovered/{prompt}"


def _make_mock_config(provider: str, model_name: str, priority: int):
    """Create a mock AIModelConfig object."""
    config = MagicMock()
    config.provider = provider
    config.model_name = model_name
    config.api_key = "test-key"
    config.api_base_url = "https://api.test.com"
    config.parameters = {}
    config.is_active = True
    config.priority = priority
    return config


# ─── Provider Registration Tests ──────────────────────────────────────────────


class TestProviderRegistration:
    """Tests for provider registration in AIServiceAdapter."""

    def test_register_provider(self):
        """Provider registration stores the class in the registry."""
        adapter = AIServiceAdapter()
        adapter.register_provider("mock_success", MockSuccessProvider)
        assert "mock_success" in adapter._provider_registry
        assert adapter._provider_registry["mock_success"] is MockSuccessProvider

    def test_register_multiple_providers(self):
        """Multiple providers can be registered."""
        adapter = AIServiceAdapter()
        adapter.register_provider("success", MockSuccessProvider)
        adapter.register_provider("fail", MockFailProvider)
        assert len(adapter._provider_registry) == 2

    def test_singleton_has_all_providers_registered(self):
        """The module-level singleton has all known providers registered."""
        assert "dashscope" in ai_adapter._provider_registry
        assert "deepseek" in ai_adapter._provider_registry
        assert "openai" in ai_adapter._provider_registry
        assert "stable_diffusion" in ai_adapter._provider_registry

    def test_singleton_provider_classes(self):
        """The singleton maps to the correct provider classes."""
        assert ai_adapter._provider_registry["dashscope"] is DashScopeProvider
        assert ai_adapter._provider_registry["deepseek"] is DeepSeekProvider
        assert ai_adapter._provider_registry["openai"] is OpenAICompatibleProvider
        assert ai_adapter._provider_registry["stable_diffusion"] is StableDiffusionProvider


# ─── Factory (get_provider) Tests ─────────────────────────────────────────────


class TestFactoryGetProvider:
    """Tests for the factory method get_provider."""

    def test_get_provider_returns_correct_instance(self):
        """get_provider returns an instance of the registered class."""
        adapter = AIServiceAdapter()
        adapter.register_provider("mock_success", MockSuccessProvider)
        config = {"model_name": "test", "api_key": "key", "api_base_url": None, "parameters": {}}
        provider = adapter.get_provider("mock_success", config)
        assert isinstance(provider, MockSuccessProvider)
        assert provider.config == config

    def test_get_provider_unknown_raises_value_error(self):
        """get_provider raises ValueError for unregistered provider names."""
        adapter = AIServiceAdapter()
        with pytest.raises(ValueError, match="Unknown provider: nonexistent"):
            adapter.get_provider("nonexistent", {})

    def test_get_provider_passes_config(self):
        """get_provider passes the config dict to the provider constructor."""
        adapter = AIServiceAdapter()
        adapter.register_provider("mock_success", MockSuccessProvider)
        config = {"model_name": "gpt-4", "api_key": "sk-123", "api_base_url": "https://api.openai.com", "parameters": {"temperature": 0.7}}
        provider = adapter.get_provider("mock_success", config)
        assert provider.config["model_name"] == "gpt-4"
        assert provider.config["parameters"]["temperature"] == 0.7


# ─── Fallback Logic Tests ─────────────────────────────────────────────────────


class TestFallbackLogic:
    """Tests for the priority-based fallback mechanism."""

    @pytest.mark.asyncio
    async def test_generate_text_success(self):
        """generate_text returns result from the first successful provider."""
        adapter = AIServiceAdapter()
        adapter.register_provider("mock_success", MockSuccessProvider)

        mock_config = _make_mock_config("mock_success", "test-model", priority=1)

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_config]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await adapter.generate_text("text_generation", "hello", mock_db)
        assert result == "generated: hello"

    @pytest.mark.asyncio
    async def test_generate_image_success(self):
        """generate_image returns result from the first successful provider."""
        adapter = AIServiceAdapter()
        adapter.register_provider("mock_success", MockSuccessProvider)

        mock_config = _make_mock_config("mock_success", "test-model", priority=1)

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_config]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await adapter.generate_image("image_generation", "a cat", mock_db)
        assert result == "https://example.com/image/a cat"

    @pytest.mark.asyncio
    async def test_fallback_on_first_provider_failure(self):
        """When the first provider fails, falls back to the next one."""
        adapter = AIServiceAdapter()
        adapter.register_provider("mock_fail", MockFailProvider)
        adapter.register_provider("mock_success", MockSuccessProvider)

        config_fail = _make_mock_config("mock_fail", "fail-model", priority=1)
        config_success = _make_mock_config("mock_success", "success-model", priority=2)

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [config_fail, config_success]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await adapter.generate_text("text_generation", "test", mock_db)
        assert result == "generated: test"

    @pytest.mark.asyncio
    async def test_fallback_image_on_first_provider_failure(self):
        """Image generation falls back to next provider on failure."""
        adapter = AIServiceAdapter()
        adapter.register_provider("mock_fail", MockFailProvider)
        adapter.register_provider("mock_success", MockSuccessProvider)

        config_fail = _make_mock_config("mock_fail", "fail-model", priority=1)
        config_success = _make_mock_config("mock_success", "success-model", priority=2)

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [config_fail, config_success]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await adapter.generate_image("image_generation", "sunset", mock_db)
        assert result == "https://example.com/image/sunset"

    @pytest.mark.asyncio
    async def test_all_providers_fail_raises_runtime_error(self):
        """When all providers fail, raises RuntimeError with last error info."""
        adapter = AIServiceAdapter()
        adapter.register_provider("mock_fail", MockFailProvider)

        config1 = _make_mock_config("mock_fail", "model-a", priority=1)
        config2 = _make_mock_config("mock_fail", "model-b", priority=2)

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [config1, config2]
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(RuntimeError, match="All providers failed"):
            await adapter.generate_text("text_generation", "test", mock_db)

    @pytest.mark.asyncio
    async def test_no_active_config_raises_runtime_error(self):
        """When no active config exists, raises RuntimeError."""
        adapter = AIServiceAdapter()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(RuntimeError, match="No active AI config found"):
            await adapter.generate_text("text_generation", "test", mock_db)

    @pytest.mark.asyncio
    async def test_no_active_config_image_raises_runtime_error(self):
        """When no active config exists for image, raises RuntimeError."""
        adapter = AIServiceAdapter()

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(RuntimeError, match="No active AI config found"):
            await adapter.generate_image("image_generation", "test", mock_db)

    @pytest.mark.asyncio
    async def test_unknown_provider_in_config_falls_back(self):
        """If a config references an unregistered provider, falls back to next."""
        adapter = AIServiceAdapter()
        adapter.register_provider("mock_success", MockSuccessProvider)

        config_unknown = _make_mock_config("unknown_provider", "model-x", priority=1)
        config_success = _make_mock_config("mock_success", "model-y", priority=2)

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [config_unknown, config_success]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await adapter.generate_text("text_generation", "hello", mock_db)
        assert result == "generated: hello"
