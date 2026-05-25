"""Stable Diffusion provider for image generation.

Uses httpx to call a Stable Diffusion API endpoint (e.g., Stability AI API
or a self-hosted SD WebUI API). Does not support text generation.
"""

import logging

import httpx

from app.services.ai_providers.base import AIProvider

logger = logging.getLogger(__name__)

# Default Stability AI API base URL
DEFAULT_SD_BASE_URL = "https://api.stability.ai"


class StableDiffusionProvider(AIProvider):
    """Stable Diffusion provider (image generation only).

    Config dict expects:
        - model_name: Model/engine identifier (e.g., 'stable-diffusion-xl-1024-v1-0')
        - api_key: Stability AI API key
        - api_base_url: Base URL (defaults to https://api.stability.ai)
        - parameters: Dict of extra params (e.g., cfg_scale, steps, style_preset)
    """

    async def generate_text(self, prompt: str, **kwargs) -> str:
        """Stable Diffusion does not support text generation.

        Raises:
            NotImplementedError: Always, as SD is image-only.
        """
        raise NotImplementedError(
            "Stable Diffusion does not support text generation. "
            "Use DashScope (Qwen) or DeepSeek for text generation."
        )

    async def generate_image(self, prompt: str, **kwargs) -> str:
        """Generate image using Stable Diffusion API.

        Calls the Stability AI text-to-image endpoint.

        Args:
            prompt: Text description of the desired image.
            **kwargs: Additional parameters (cfg_scale, steps, style_preset, etc.)

        Returns:
            URL or base64 data of the generated image.

        Raises:
            RuntimeError: If the API call fails.
        """
        api_key = self.config.get("api_key")
        model_name = self.config.get("model_name", "stable-diffusion-xl-1024-v1-0")
        base_url = self.config.get("api_base_url") or DEFAULT_SD_BASE_URL
        parameters = self.config.get("parameters", {})

        # Merge kwargs into parameters
        merged_params = {**parameters, **kwargs}
        cfg_scale = merged_params.pop("cfg_scale", 7)
        steps = merged_params.pop("steps", 30)
        width = merged_params.pop("width", 1024)
        height = merged_params.pop("height", 1024)
        style_preset = merged_params.pop("style_preset", None)

        # Build request payload for Stability AI API
        payload = {
            "text_prompts": [{"text": prompt, "weight": 1.0}],
            "cfg_scale": cfg_scale,
            "steps": steps,
            "width": width,
            "height": height,
        }
        if style_preset:
            payload["style_preset"] = style_preset

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        url = (
            f"{base_url.rstrip('/')}/v1/generation/{model_name}/text-to-image"
        )

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, json=payload, headers=headers)

            if response.status_code != 200:
                error_detail = response.text
                logger.error(
                    f"Stable Diffusion API error: status={response.status_code}, "
                    f"detail={error_detail}"
                )
                raise RuntimeError(
                    f"Stable Diffusion API error (status {response.status_code}): {error_detail}"
                )

            data = response.json()
            # Stability AI returns artifacts array with base64 or URL
            artifacts = data.get("artifacts", [])
            if not artifacts:
                raise RuntimeError("Stable Diffusion returned no image artifacts")

            # Return the first artifact - could be base64 or a URL depending on config
            artifact = artifacts[0]
            if "url" in artifact:
                return artifact["url"]
            elif "base64" in artifact:
                # Return as data URI for downstream processing
                return f"data:image/png;base64,{artifact['base64']}"
            else:
                raise RuntimeError("Stable Diffusion artifact has no url or base64 data")

        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"Stable Diffusion image generation exception: {e}")
            raise RuntimeError(f"Stable Diffusion image generation failed: {e}") from e
