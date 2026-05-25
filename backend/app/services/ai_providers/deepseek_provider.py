"""DeepSeek provider for text generation.

Uses httpx to call the DeepSeek API which follows OpenAI-compatible format.
DeepSeek does not support image generation.
"""

import logging

import httpx

from app.services.ai_providers.base import AIProvider

logger = logging.getLogger(__name__)

# Default DeepSeek API base URL
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"


class DeepSeekProvider(AIProvider):
    """DeepSeek provider (text generation only, OpenAI-compatible format).

    Config dict expects:
        - model_name: Model identifier (e.g., 'deepseek-chat', 'deepseek-coder')
        - api_key: DeepSeek API key
        - api_base_url: Optional custom base URL (defaults to https://api.deepseek.com)
        - parameters: Dict of extra params (e.g., temperature, max_tokens)
    """

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using DeepSeek API (OpenAI-compatible format).

        Args:
            prompt: The text prompt to generate content from.
            **kwargs: Additional parameters (system_prompt, temperature, etc.)

        Returns:
            Generated text content.

        Raises:
            RuntimeError: If the API call fails.
        """
        api_key = self.config.get("api_key")
        model_name = self.config.get("model_name", "deepseek-chat")
        base_url = self.config.get("api_base_url") or DEFAULT_DEEPSEEK_BASE_URL
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
        for key in ("temperature", "top_p", "max_tokens", "stream"):
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
                    f"DeepSeek API error: status={response.status_code}, "
                    f"detail={error_detail}"
                )
                raise RuntimeError(
                    f"DeepSeek API error (status {response.status_code}): {error_detail}"
                )

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content

        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"DeepSeek text generation exception: {e}")
            raise RuntimeError(f"DeepSeek text generation failed: {e}") from e

    async def generate_image(self, prompt: str, **kwargs) -> str:
        """DeepSeek does not support image generation.

        Raises:
            NotImplementedError: Always, as DeepSeek is text-only.
        """
        raise NotImplementedError(
            "DeepSeek does not support image generation. "
            "Use DashScope (Wanx) or Stable Diffusion for image generation."
        )
