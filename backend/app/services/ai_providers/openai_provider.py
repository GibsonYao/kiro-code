"""OpenAI-compatible provider for text and image generation.

Uses httpx to call any OpenAI-compatible API endpoint (OpenAI, Azure OpenAI,
local LLM servers, etc.) for both text (chat completions) and image (DALL-E
compatible) generation.
"""

import logging

import httpx

from app.services.ai_providers.base import AIProvider

logger = logging.getLogger(__name__)

# Default OpenAI API base URL
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com"


class OpenAICompatibleProvider(AIProvider):
    """OpenAI-compatible provider (generic OpenAI API interface).

    Config dict expects:
        - model_name: Model identifier (e.g., 'gpt-4', 'gpt-3.5-turbo')
        - api_key: API key for the service
        - api_base_url: Base URL of the OpenAI-compatible API
        - parameters: Dict of extra params (e.g., temperature, max_tokens)
    """

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using any OpenAI-compatible chat completions API.

        Args:
            prompt: The text prompt to generate content from.
            **kwargs: Additional parameters (system_prompt, temperature, etc.)

        Returns:
            Generated text content.

        Raises:
            RuntimeError: If the API call fails.
        """
        api_key = self.config.get("api_key")
        model_name = self.config.get("model_name", "gpt-3.5-turbo")
        base_url = self.config.get("api_base_url") or DEFAULT_OPENAI_BASE_URL
        parameters = self.config.get("parameters", {})

        # Merge kwargs into parameters
        merged_params = {**parameters, **kwargs}
        system_prompt = merged_params.pop("system_prompt", None)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Build request payload
        payload = {
            "model": model_name,
            "messages": messages,
        }
        # Add optional parameters
        for key in ("temperature", "top_p", "max_tokens", "stream", "frequency_penalty", "presence_penalty"):
            if key in merged_params:
                payload[key] = merged_params[key]

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        url = f"{base_url.rstrip('/')}/v1/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=headers)

            if response.status_code != 200:
                error_detail = response.text
                logger.error(
                    f"OpenAI-compatible API error: status={response.status_code}, "
                    f"detail={error_detail}"
                )
                raise RuntimeError(
                    f"OpenAI-compatible API error (status {response.status_code}): {error_detail}"
                )

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content

        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"OpenAI-compatible text generation exception: {e}")
            raise RuntimeError(f"OpenAI-compatible text generation failed: {e}") from e

    async def generate_image(self, prompt: str, **kwargs) -> str:
        """Generate image using DALL-E compatible endpoint.

        Args:
            prompt: Text description of the desired image.
            **kwargs: Additional parameters (size, quality, style, n, etc.)

        Returns:
            URL of the generated image.

        Raises:
            RuntimeError: If the API call fails.
        """
        api_key = self.config.get("api_key")
        model_name = self.config.get("model_name", "dall-e-3")
        base_url = self.config.get("api_base_url") or DEFAULT_OPENAI_BASE_URL
        parameters = self.config.get("parameters", {})

        # Merge kwargs into parameters
        merged_params = {**parameters, **kwargs}
        size = merged_params.pop("size", "1024x1024")
        quality = merged_params.pop("quality", "standard")
        n = merged_params.pop("n", 1)

        payload = {
            "model": model_name,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": n,
            "response_format": "url",
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        url = f"{base_url.rstrip('/')}/v1/images/generations"

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload, headers=headers)

            if response.status_code != 200:
                error_detail = response.text
                logger.error(
                    f"OpenAI-compatible image API error: status={response.status_code}, "
                    f"detail={error_detail}"
                )
                raise RuntimeError(
                    f"OpenAI-compatible image API error (status {response.status_code}): {error_detail}"
                )

            data = response.json()
            image_url = data["data"][0]["url"]
            return image_url

        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"OpenAI-compatible image generation exception: {e}")
            raise RuntimeError(f"OpenAI-compatible image generation failed: {e}") from e
