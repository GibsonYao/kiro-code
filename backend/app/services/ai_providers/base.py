"""Abstract base class for AI providers.

This module is separate to avoid circular imports between ai_service.py
and the concrete provider implementations.
"""

from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Abstract base class for AI providers.

    All provider implementations must inherit from this class and implement
    the generate_text and generate_image methods.
    """

    def __init__(self, config: dict):
        """Initialize provider with configuration.

        Args:
            config: Dictionary containing provider-specific configuration
                    (model_name, api_key, api_base_url, parameters, etc.)
        """
        self.config = config

    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text content based on the given prompt.

        Args:
            prompt: The text prompt to generate content from.
            **kwargs: Additional provider-specific parameters.

        Returns:
            Generated text content.
        """
        ...

    @abstractmethod
    async def generate_image(self, prompt: str, **kwargs) -> str:
        """Generate an image based on the given prompt.

        Args:
            prompt: The text prompt describing the desired image.
            **kwargs: Additional provider-specific parameters.

        Returns:
            URL of the generated image.
        """
        ...
