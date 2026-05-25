"""Tests for AI provider implementations.

Tests verify:
- Each provider can be instantiated with config
- Text generation works correctly (mocked HTTP/SDK responses)
- Image generation works correctly (mocked HTTP/SDK responses)
- Error handling works (mocked error responses)
- NotImplementedError raised where appropriate
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.ai_providers import (
    DashScopeProvider,
    DeepSeekProvider,
    OpenAICompatibleProvider,
    StableDiffusionProvider,
)


# ─── Shared Config Fixtures ───────────────────────────────────────────────────


@pytest.fixture
def dashscope_config():
    return {
        "model_name": "qwen-turbo",
        "api_key": "sk-test-dashscope-key",
        "api_base_url": None,
        "parameters": {"temperature": 0.7},
    }


@pytest.fixture
def deepseek_config():
    return {
        "model_name": "deepseek-chat",
        "api_key": "sk-test-deepseek-key",
        "api_base_url": "https://api.deepseek.com",
        "parameters": {"temperature": 0.8},
    }


@pytest.fixture
def openai_config():
    return {
        "model_name": "gpt-4",
        "api_key": "sk-test-openai-key",
        "api_base_url": "https://api.openai.com",
        "parameters": {"temperature": 0.5},
    }


@pytest.fixture
def sd_config():
    return {
        "model_name": "stable-diffusion-xl-1024-v1-0",
        "api_key": "sk-test-stability-key",
        "api_base_url": "https://api.stability.ai",
        "parameters": {"steps": 30, "cfg_scale": 7},
    }


# ─── DashScopeProvider Tests ─────────────────────────────────────────────────


class TestDashScopeProvider:
    """Tests for DashScopeProvider."""

    def test_instantiation(self, dashscope_config):
        """Provider can be instantiated with config dict."""
        provider = DashScopeProvider(dashscope_config)
        assert provider.config == dashscope_config
        assert provider.config["model_name"] == "qwen-turbo"

    @pytest.mark.asyncio
    async def test_generate_text_success(self, dashscope_config):
        """Text generation returns content on successful API call."""
        import sys

        provider = DashScopeProvider(dashscope_config)

        # Mock the dashscope Generation.call response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.output.choices = [
            MagicMock(message=MagicMock(content="Hello, this is generated text."))
        ]

        mock_dashscope = MagicMock()
        mock_dashscope.Generation.call.return_value = mock_response

        with patch.dict(sys.modules, {"dashscope": mock_dashscope}):
            result = await provider.generate_text("Tell me a story")

        assert result == "Hello, this is generated text."
        mock_dashscope.Generation.call.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_text_api_error(self, dashscope_config):
        """Text generation raises RuntimeError on API error."""
        import sys

        provider = DashScopeProvider(dashscope_config)

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.message = "Invalid request"

        mock_dashscope = MagicMock()
        mock_dashscope.Generation.call.return_value = mock_response

        with patch.dict(sys.modules, {"dashscope": mock_dashscope}):
            with pytest.raises(RuntimeError, match="DashScope API error"):
                await provider.generate_text("bad prompt")

    @pytest.mark.asyncio
    async def test_generate_text_exception(self, dashscope_config):
        """Text generation raises RuntimeError on unexpected exception."""
        import sys

        provider = DashScopeProvider(dashscope_config)

        mock_dashscope = MagicMock()
        mock_dashscope.Generation.call.side_effect = ConnectionError("Network error")

        with patch.dict(sys.modules, {"dashscope": mock_dashscope}):
            with pytest.raises(RuntimeError, match="DashScope text generation failed"):
                await provider.generate_text("test")

    @pytest.mark.asyncio
    async def test_generate_image_success(self, dashscope_config):
        """Image generation returns URL on successful API call."""
        import sys

        config = {**dashscope_config, "model_name": "wanx-v1"}
        provider = DashScopeProvider(config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.output.results = [MagicMock(url="https://oss.example.com/image.png")]

        mock_dashscope = MagicMock()
        mock_dashscope.ImageSynthesis.call.return_value = mock_response

        with patch.dict(sys.modules, {"dashscope": mock_dashscope}):
            result = await provider.generate_image("A beautiful sunset")

        assert result == "https://oss.example.com/image.png"

    @pytest.mark.asyncio
    async def test_generate_image_api_error(self, dashscope_config):
        """Image generation raises RuntimeError on API error."""
        import sys

        provider = DashScopeProvider(dashscope_config)

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.message = "Internal server error"

        mock_dashscope = MagicMock()
        mock_dashscope.ImageSynthesis.call.return_value = mock_response

        with patch.dict(sys.modules, {"dashscope": mock_dashscope}):
            with pytest.raises(RuntimeError, match="DashScope API error"):
                await provider.generate_image("test")

    @pytest.mark.asyncio
    async def test_generate_image_no_results(self, dashscope_config):
        """Image generation raises RuntimeError when no results returned."""
        import sys

        provider = DashScopeProvider(dashscope_config)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.output.results = []

        mock_dashscope = MagicMock()
        mock_dashscope.ImageSynthesis.call.return_value = mock_response

        with patch.dict(sys.modules, {"dashscope": mock_dashscope}):
            with pytest.raises(RuntimeError, match="returned no results"):
                await provider.generate_image("test")


# ─── DeepSeekProvider Tests ───────────────────────────────────────────────────


class TestDeepSeekProvider:
    """Tests for DeepSeekProvider."""

    def test_instantiation(self, deepseek_config):
        """Provider can be instantiated with config dict."""
        provider = DeepSeekProvider(deepseek_config)
        assert provider.config == deepseek_config
        assert provider.config["model_name"] == "deepseek-chat"

    @pytest.mark.asyncio
    async def test_generate_text_success(self, deepseek_config):
        """Text generation returns content on successful API call."""
        provider = DeepSeekProvider(deepseek_config)

        mock_response = httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {"message": {"content": "DeepSeek generated text."}}
                ]
            },
        )

        with patch("app.services.ai_providers.deepseek_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            result = await provider.generate_text("Hello DeepSeek")

        assert result == "DeepSeek generated text."

    @pytest.mark.asyncio
    async def test_generate_text_api_error(self, deepseek_config):
        """Text generation raises RuntimeError on non-200 response."""
        provider = DeepSeekProvider(deepseek_config)

        mock_response = httpx.Response(
            status_code=429,
            text="Rate limit exceeded",
        )

        with patch("app.services.ai_providers.deepseek_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            with pytest.raises(RuntimeError, match="DeepSeek API error"):
                await provider.generate_text("test")

    @pytest.mark.asyncio
    async def test_generate_text_network_error(self, deepseek_config):
        """Text generation raises RuntimeError on network exception."""
        provider = DeepSeekProvider(deepseek_config)

        with patch("app.services.ai_providers.deepseek_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.ConnectError("Connection refused")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            with pytest.raises(RuntimeError, match="DeepSeek text generation failed"):
                await provider.generate_text("test")

    @pytest.mark.asyncio
    async def test_generate_image_not_implemented(self, deepseek_config):
        """Image generation raises NotImplementedError."""
        provider = DeepSeekProvider(deepseek_config)
        with pytest.raises(NotImplementedError, match="does not support image generation"):
            await provider.generate_image("test")


# ─── OpenAICompatibleProvider Tests ───────────────────────────────────────────


class TestOpenAICompatibleProvider:
    """Tests for OpenAICompatibleProvider."""

    def test_instantiation(self, openai_config):
        """Provider can be instantiated with config dict."""
        provider = OpenAICompatibleProvider(openai_config)
        assert provider.config == openai_config
        assert provider.config["model_name"] == "gpt-4"

    @pytest.mark.asyncio
    async def test_generate_text_success(self, openai_config):
        """Text generation returns content on successful API call."""
        provider = OpenAICompatibleProvider(openai_config)

        mock_response = httpx.Response(
            status_code=200,
            json={
                "choices": [
                    {"message": {"content": "OpenAI generated text."}}
                ]
            },
        )

        with patch("app.services.ai_providers.openai_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            result = await provider.generate_text("Hello OpenAI")

        assert result == "OpenAI generated text."

    @pytest.mark.asyncio
    async def test_generate_text_api_error(self, openai_config):
        """Text generation raises RuntimeError on non-200 response."""
        provider = OpenAICompatibleProvider(openai_config)

        mock_response = httpx.Response(
            status_code=401,
            text="Unauthorized",
        )

        with patch("app.services.ai_providers.openai_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            with pytest.raises(RuntimeError, match="OpenAI-compatible API error"):
                await provider.generate_text("test")

    @pytest.mark.asyncio
    async def test_generate_image_success(self, openai_config):
        """Image generation returns URL on successful API call."""
        provider = OpenAICompatibleProvider(openai_config)

        mock_response = httpx.Response(
            status_code=200,
            json={
                "data": [{"url": "https://oaidalleapiprodscus.blob.core.windows.net/image.png"}]
            },
        )

        with patch("app.services.ai_providers.openai_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            result = await provider.generate_image("A cat painting")

        assert result == "https://oaidalleapiprodscus.blob.core.windows.net/image.png"

    @pytest.mark.asyncio
    async def test_generate_image_api_error(self, openai_config):
        """Image generation raises RuntimeError on non-200 response."""
        provider = OpenAICompatibleProvider(openai_config)

        mock_response = httpx.Response(
            status_code=500,
            text="Internal Server Error",
        )

        with patch("app.services.ai_providers.openai_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            with pytest.raises(RuntimeError, match="OpenAI-compatible image API error"):
                await provider.generate_image("test")


# ─── StableDiffusionProvider Tests ────────────────────────────────────────────


class TestStableDiffusionProvider:
    """Tests for StableDiffusionProvider."""

    def test_instantiation(self, sd_config):
        """Provider can be instantiated with config dict."""
        provider = StableDiffusionProvider(sd_config)
        assert provider.config == sd_config
        assert provider.config["model_name"] == "stable-diffusion-xl-1024-v1-0"

    @pytest.mark.asyncio
    async def test_generate_text_not_implemented(self, sd_config):
        """Text generation raises NotImplementedError."""
        provider = StableDiffusionProvider(sd_config)
        with pytest.raises(NotImplementedError, match="does not support text generation"):
            await provider.generate_text("test")

    @pytest.mark.asyncio
    async def test_generate_image_success_url(self, sd_config):
        """Image generation returns URL when artifact has url field."""
        provider = StableDiffusionProvider(sd_config)

        mock_response = httpx.Response(
            status_code=200,
            json={
                "artifacts": [{"url": "https://stability.ai/generated/image.png"}]
            },
        )

        with patch("app.services.ai_providers.stable_diffusion_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            result = await provider.generate_image("A mountain landscape")

        assert result == "https://stability.ai/generated/image.png"

    @pytest.mark.asyncio
    async def test_generate_image_success_base64(self, sd_config):
        """Image generation returns data URI when artifact has base64 field."""
        provider = StableDiffusionProvider(sd_config)

        mock_response = httpx.Response(
            status_code=200,
            json={
                "artifacts": [{"base64": "iVBORw0KGgoAAAANS..."}]
            },
        )

        with patch("app.services.ai_providers.stable_diffusion_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            result = await provider.generate_image("A mountain landscape")

        assert result.startswith("data:image/png;base64,")

    @pytest.mark.asyncio
    async def test_generate_image_api_error(self, sd_config):
        """Image generation raises RuntimeError on non-200 response."""
        provider = StableDiffusionProvider(sd_config)

        mock_response = httpx.Response(
            status_code=403,
            text="Forbidden",
        )

        with patch("app.services.ai_providers.stable_diffusion_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            with pytest.raises(RuntimeError, match="Stable Diffusion API error"):
                await provider.generate_image("test")

    @pytest.mark.asyncio
    async def test_generate_image_no_artifacts(self, sd_config):
        """Image generation raises RuntimeError when no artifacts returned."""
        provider = StableDiffusionProvider(sd_config)

        mock_response = httpx.Response(
            status_code=200,
            json={"artifacts": []},
        )

        with patch("app.services.ai_providers.stable_diffusion_provider.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            with pytest.raises(RuntimeError, match="no image artifacts"):
                await provider.generate_image("test")


# ─── Integration: Import from ai_service still works ──────────────────────────


class TestAIServiceImports:
    """Verify that importing providers from ai_service.py still works."""

    def test_import_from_ai_service(self):
        """Providers can still be imported from ai_service module."""
        from app.services.ai_service import (
            DashScopeProvider as DS,
            DeepSeekProvider as DSK,
            OpenAICompatibleProvider as OAI,
            StableDiffusionProvider as SD,
        )
        assert DS is DashScopeProvider
        assert DSK is DeepSeekProvider
        assert OAI is OpenAICompatibleProvider
        assert SD is StableDiffusionProvider

    def test_ai_adapter_uses_new_providers(self):
        """The module-level ai_adapter uses the new provider implementations."""
        from app.services.ai_service import ai_adapter

        provider = ai_adapter.get_provider(
            "dashscope",
            {"model_name": "qwen-turbo", "api_key": "test", "api_base_url": None, "parameters": {}},
        )
        assert isinstance(provider, DashScopeProvider)
