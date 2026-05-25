"""AI service adapter for text and image generation.

Implements a factory pattern with fallback mechanism:
- AIProvider: Abstract base class for all AI providers (defined in ai_providers.base)
- AIServiceAdapter: Factory that routes requests to the correct provider
- Providers: DashScope, DeepSeek, OpenAI-compatible, StableDiffusion
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_cached, invalidate_ai_config_cache, set_cached
from app.models.ai_config import AIModelConfig
from app.services.ai_providers import (
    AIProvider,
    DashScopeProvider,
    DeepSeekProvider,
    OpenAICompatibleProvider,
    StableDiffusionProvider,
)

# Re-export AIProvider for backward compatibility
__all__ = [
    "AIProvider",
    "AIServiceAdapter",
    "DashScopeProvider",
    "DeepSeekProvider",
    "OpenAICompatibleProvider",
    "StableDiffusionProvider",
    "ai_adapter",
    "invalidate_ai_config_cache",
]

logger = logging.getLogger(__name__)


class AIServiceAdapter:
    """Factory class that routes AI requests to the correct provider.

    Implements:
    - Provider registration (factory pattern)
    - Config-based provider instantiation
    - Priority-based fallback on failure
    """

    def __init__(self):
        """Initialize with empty provider registry."""
        self._provider_registry: dict[str, type[AIProvider]] = {}

    def register_provider(self, provider_name: str, provider_class: type[AIProvider]) -> None:
        """Register a provider class by name.

        Args:
            provider_name: Unique identifier for the provider (e.g., 'dashscope').
            provider_class: The provider class to register.
        """
        self._provider_registry[provider_name] = provider_class

    def get_provider(self, provider_name: str, config: dict) -> AIProvider:
        """Instantiate a provider with the given configuration.

        Args:
            provider_name: Name of the registered provider.
            config: Configuration dictionary to pass to the provider.

        Returns:
            An instance of the requested provider.

        Raises:
            ValueError: If the provider name is not registered.
        """
        provider_class = self._provider_registry.get(provider_name)
        if provider_class is None:
            raise ValueError(f"Unknown provider: {provider_name}")
        return provider_class(config)

    async def _load_configs(self, config_key: str, db: AsyncSession) -> list[AIModelConfig]:
        """Load active AI model configs for a given config_key, ordered by priority.

        First checks Redis cache. On cache miss, queries the database and
        populates the cache with a 5-minute TTL.

        Args:
            config_key: The type of generation (e.g., 'text_generation', 'image_generation').
            db: Async database session.

        Returns:
            List of active AIModelConfig records sorted by priority (ascending = higher priority).
        """
        cache_key = f"ai_config:{config_key}"

        # Try cache first
        cached_data = await get_cached(cache_key)
        if cached_data is not None:
            logger.debug(f"Cache hit for config_key={config_key}")
            # Reconstruct AIModelConfig instances from cached dicts
            configs = []
            for item in cached_data:
                config = AIModelConfig()
                config.id = item.get("id")
                config.config_key = item["config_key"]
                config.provider = item["provider"]
                config.model_name = item["model_name"]
                config.api_key = item["api_key"]
                config.api_base_url = item.get("api_base_url")
                config.parameters = item.get("parameters")
                config.is_active = item.get("is_active", True)
                config.priority = item.get("priority", 0)
                configs.append(config)
            return configs

        # Cache miss - query DB
        logger.debug(f"Cache miss for config_key={config_key}, querying DB")
        result = await db.execute(
            select(AIModelConfig)
            .where(AIModelConfig.config_key == config_key)
            .where(AIModelConfig.is_active == True)  # noqa: E712
            .order_by(AIModelConfig.priority.asc())
        )
        configs = list(result.scalars().all())

        # Serialize and cache
        if configs:
            serialized = [
                {
                    "id": str(config.id) if config.id else None,
                    "config_key": config.config_key,
                    "provider": config.provider,
                    "model_name": config.model_name,
                    "api_key": config.api_key,
                    "api_base_url": config.api_base_url,
                    "parameters": config.parameters,
                    "is_active": config.is_active,
                    "priority": config.priority,
                }
                for config in configs
            ]
            await set_cached(cache_key, serialized, ttl=300)

        return configs

    async def generate_text(
        self, config_key: str, prompt: str, db: AsyncSession, **kwargs
    ) -> str:
        """Generate text using the configured provider with fallback.

        Loads active configs for the config_key, tries each provider by priority.
        Falls back to the next provider on failure.

        Args:
            config_key: The configuration key (e.g., 'text_generation', 'vision_story').
            prompt: The text prompt.
            db: Async database session.
            **kwargs: Additional parameters passed to the provider.

        Returns:
            Generated text content.

        Raises:
            RuntimeError: If all providers fail or no active config is found.
        """
        configs = await self._load_configs(config_key, db)
        if not configs:
            raise RuntimeError(f"No active AI config found for key: {config_key}")

        last_error: Exception | None = None
        for config in configs:
            try:
                provider = self.get_provider(
                    config.provider,
                    {
                        "model_name": config.model_name,
                        "api_key": config.api_key,
                        "api_base_url": config.api_base_url,
                        "parameters": config.parameters or {},
                    },
                )
                result = await provider.generate_text(prompt, **kwargs)
                return result
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Provider {config.provider} (model={config.model_name}) failed "
                    f"for text generation: {e}. Trying next provider..."
                )
                continue

        raise RuntimeError(
            f"All providers failed for config_key={config_key}. "
            f"Last error: {last_error}"
        )

    async def generate_image(
        self, config_key: str, prompt: str, db: AsyncSession, **kwargs
    ) -> str:
        """Generate an image using the configured provider with fallback.

        Loads active configs for the config_key, tries each provider by priority.
        Falls back to the next provider on failure.

        Args:
            config_key: The configuration key (e.g., 'image_generation').
            prompt: The text prompt describing the desired image.
            db: Async database session.
            **kwargs: Additional parameters passed to the provider.

        Returns:
            URL of the generated image.

        Raises:
            RuntimeError: If all providers fail or no active config is found.
        """
        configs = await self._load_configs(config_key, db)
        if not configs:
            raise RuntimeError(f"No active AI config found for key: {config_key}")

        last_error: Exception | None = None
        for config in configs:
            try:
                provider = self.get_provider(
                    config.provider,
                    {
                        "model_name": config.model_name,
                        "api_key": config.api_key,
                        "api_base_url": config.api_base_url,
                        "parameters": config.parameters or {},
                    },
                )
                result = await provider.generate_image(prompt, **kwargs)
                return result
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Provider {config.provider} (model={config.model_name}) failed "
                    f"for image generation: {e}. Trying next provider..."
                )
                continue

        raise RuntimeError(
            f"All providers failed for config_key={config_key}. "
            f"Last error: {last_error}"
        )


# Module-level singleton with all known providers registered
ai_adapter = AIServiceAdapter()
ai_adapter.register_provider("dashscope", DashScopeProvider)
ai_adapter.register_provider("deepseek", DeepSeekProvider)
ai_adapter.register_provider("openai", OpenAICompatibleProvider)
ai_adapter.register_provider("stable_diffusion", StableDiffusionProvider)
