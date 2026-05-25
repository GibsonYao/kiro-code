"""DashScope provider for text and image generation.

Uses the dashscope SDK to call:
- Qwen models (通义千问) for text generation
- Wanx models (通义万相) for image generation
"""

import logging

from app.services.ai_providers.base import AIProvider

logger = logging.getLogger(__name__)


class DashScopeProvider(AIProvider):
    """DashScope provider (通义千问 text + 通义万相 image generation).

    Config dict expects:
        - model_name: Model identifier (e.g., 'qwen-turbo', 'wanx-v1')
        - api_key: DashScope API key
        - api_base_url: Optional custom base URL (unused for SDK calls)
        - parameters: Dict of extra params (e.g., temperature, image_size)
    """

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using DashScope Qwen model.

        Uses the dashscope SDK Generation.call() API in async-compatible manner.

        Args:
            prompt: The text prompt to generate content from.
            **kwargs: Additional parameters (system_prompt, temperature, etc.)

        Returns:
            Generated text content.

        Raises:
            RuntimeError: If the API call fails or returns an error status.
        """
        import dashscope
        from dashscope import Generation

        api_key = self.config.get("api_key")
        model_name = self.config.get("model_name", "qwen-turbo")
        parameters = self.config.get("parameters", {})

        # Merge kwargs into parameters (kwargs take precedence)
        merged_params = {**parameters, **kwargs}
        system_prompt = merged_params.pop("system_prompt", None)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = Generation.call(
                model=model_name,
                messages=messages,
                api_key=api_key,
                result_format="message",
                **{k: v for k, v in merged_params.items() if k in ("temperature", "top_p", "max_tokens")},
            )

            if response.status_code != 200:
                error_msg = getattr(response, "message", "Unknown error")
                logger.error(
                    f"DashScope text generation failed: status={response.status_code}, "
                    f"message={error_msg}"
                )
                raise RuntimeError(
                    f"DashScope API error (status {response.status_code}): {error_msg}"
                )

            # Extract text from response
            content = response.output.choices[0].message.content
            return content

        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"DashScope text generation exception: {e}")
            raise RuntimeError(f"DashScope text generation failed: {e}") from e

    async def generate_image(self, prompt: str, **kwargs) -> str:
        """Generate image using DashScope Wanx model.

        Uses the dashscope ImageSynthesis API for image generation.

        Args:
            prompt: Text description of the desired image.
            **kwargs: Additional parameters (size, style, n, etc.)

        Returns:
            URL of the generated image.

        Raises:
            RuntimeError: If the API call fails or returns an error status.
        """
        from dashscope import ImageSynthesis

        api_key = self.config.get("api_key")
        model_name = self.config.get("model_name", "wanx-v1")
        parameters = self.config.get("parameters", {})

        # Merge kwargs into parameters
        merged_params = {**parameters, **kwargs}
        size = merged_params.pop("size", "1024*1024")
        n = merged_params.pop("n", 1)

        try:
            response = ImageSynthesis.call(
                model=model_name,
                input={"prompt": prompt},
                parameters={"size": size, "n": n},
                api_key=api_key,
            )

            if response.status_code != 200:
                error_msg = getattr(response, "message", "Unknown error")
                logger.error(
                    f"DashScope image generation failed: status={response.status_code}, "
                    f"message={error_msg}"
                )
                raise RuntimeError(
                    f"DashScope API error (status {response.status_code}): {error_msg}"
                )

            # Extract image URL from response
            results = response.output.results
            if not results:
                raise RuntimeError("DashScope image generation returned no results")

            image_url = results[0].url
            return image_url

        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"DashScope image generation exception: {e}")
            raise RuntimeError(f"DashScope image generation failed: {e}") from e
