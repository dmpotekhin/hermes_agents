"""Abacus AI ImageGenProvider implementation.

Provides image generation through Abacus AI's RouteLLM API.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

import requests

try:
    from agent.image_gen_provider import (
        DEFAULT_ASPECT_RATIO,
        ImageGenProvider,
        error_response,
        resolve_aspect_ratio,
        save_b64_image,
        save_url_image,
        success_response,
    )
except ImportError:
    # Standalone / CI mode — Hermes agent SDK not available.
    # The provider cannot be used without it, but submodules (models,
    # utils, config) can still be imported for testing.
    ImageGenProvider = object  # type: ignore
    DEFAULT_ASPECT_RATIO = "square"
    def error_response(**kwargs): return {"status": "error", **kwargs}
    def success_response(**kwargs): return {"status": "success", **kwargs}
    def resolve_aspect_ratio(r): return r
    def save_b64_image(*a, **kw): return ""
    def save_url_image(*a, **kw): return ""

from .config import resolve_credentials, resolve_model_chain
from .models import (
    MODEL_CATALOG,
    _REQUEST_TIMEOUT,
    DEFAULT_MODEL,
    resolve_aspect_ratio_for_model,
)
from .utils import to_image_url_part, detect_image_format, strip_data_url_prefix

logger = logging.getLogger(__name__)


class AbacusAIImageProvider(ImageGenProvider):
    """Image generation via Abacus AI RouteLLM.

    Provides access to 20+ image generation models through Abacus AI's
    OpenAI-compatible RouteLLM API, including FLUX, DALL-E, MidJourney,
    and more.
    """

    @property
    def name(self) -> str:
        return "abacus_ai"

    @property
    def display_name(self) -> str:
        return "Abacus AI"

    # ------------------------------------------------------------------
    # Availability & credentials
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        try:
            _, api_key = resolve_credentials()
            return bool(api_key)
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Model information
    # ------------------------------------------------------------------

    def list_models(self) -> List[Dict[str, Any]]:
        return list(MODEL_CATALOG)

    def default_model(self) -> Optional[str]:
        return DEFAULT_MODEL

    def capabilities(self) -> Dict[str, Any]:
        return {
            "modalities": ["text", "image"],
            "max_reference_images": 3,
        }

    def get_setup_schema(self) -> Dict[str, Any]:
        from .config import ABACUS_AI_DEFAULT_BASE_URL

        return {
            "name": "Abacus AI (RouteLLM)",
            "badge": "paid",
            "tag": (
                "FLUX, DALL-E, MidJourney, and 20+ models via Abacus AI "
                "RouteLLM. Uses credentials from custom_providers in config.yaml "
                "or ABACUS_AI_API_KEY env var."
            ),
            "config_keys": {
                "baseUrl": {
                    "label": "Base URL",
                    "placeholder": ABACUS_AI_DEFAULT_BASE_URL,
                },
                "apiKey": {
                    "label": "API Key",
                    "placeholder": "s2_...",
                    "secret": True,
                },
            },
            "env_vars": [
                {
                    "key": "ABACUS_AI_API_KEY",
                    "prompt": "Abacus AI API key",
                    "url": "https://abacus.ai/app/route-llm-apis",
                },
            ],
        }

    # ------------------------------------------------------------------
    # Image generation
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        *,
        image_url: Optional[str] = None,
        reference_image_urls: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        prompt = (prompt or "").strip()
        aspect = resolve_aspect_ratio(aspect_ratio)

        if not prompt:
            return error_response(
                error="Prompt is required and must be a non-empty string",
                error_type="invalid_argument",
                provider="abacus_ai",
                aspect_ratio=aspect,
            )

        base_url, api_key = resolve_credentials()
        if not api_key:
            return error_response(
                error=(
                    "Abacus AI API key not found. Configure it under "
                    "custom_providers in config.yaml or set ABACUS_AI_API_KEY."
                ),
                error_type="auth_required",
                provider="abacus_ai",
                aspect_ratio=aspect,
            )

        model_chain = resolve_model_chain(kwargs.get("model"))
        model_id = model_chain[0]

        # Resolve aspect ratio based on model
        or_aspect = resolve_aspect_ratio_for_model(aspect, model_id)

        # Collect reference images
        references: List[str] = []
        for ref in kwargs.get("reference_images") or []:
            references.append(str(ref))
        if image_url:
            references.append(str(image_url))
        for ref in reference_image_urls or []:
            references.append(str(ref))

        content: List[Dict[str, Any]] = [
            {"type": "text", "text": prompt}
        ]
        for ref in references[:3]:
            part = to_image_url_part(ref)
            if part:
                content.append(
                    {"type": "image_url", "image_url": {"url": part}}
                )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Build image_config with supported parameters
        image_config: Dict[str, Any] = {
            "aspect_ratio": or_aspect,
        }

        # Optional: number of images (supported by some models)
        num_images = kwargs.get("num_images")
        if num_images and 1 <= int(num_images) <= 4:
            image_config["num_images"] = int(num_images)

        # Optional quality parameter (OpenAI models)
        quality = kwargs.get("quality")
        if quality:
            image_config["quality"] = quality

        # Optional resolution parameter (nano_banana_pro, nano_banana2, imagen)
        resolution = kwargs.get("resolution") or kwargs.get("res")
        if resolution:
            image_config["resolution"] = str(resolution)

        # Optional prompt rewriting (enabled by default for better results)
        rewrite = kwargs.get("rewrite_prompt")
        if rewrite is not None:
            image_config["rewrite_prompt"] = rewrite

        payload: Dict[str, Any] = {
            "model": model_id,
            "modalities": ["image", "text"],
            "messages": [{"role": "user", "content": content}],
            "image_config": image_config,
        }

        try:
            response = requests.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=_REQUEST_TIMEOUT,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Abacus AI image gen failed: %s", exc)
            return error_response(
                error=str(exc),
                error_type="api_error",
                provider="abacus_ai",
                aspect_ratio=aspect,
                model=model_id,
            )

        try:
            data = response.json()
        except (json.JSONDecodeError, ValueError) as exc:
            return error_response(
                error="Invalid JSON response",
                error_type="api_error",
                provider="abacus_ai",
                aspect_ratio=aspect,
                model=model_id,
            )

        # Extract image from response
        image = self._extract_image(data, model_id)
        if image:
            return success_response(
                image=image,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
                provider="abacus_ai",
            )

        return error_response(
            error="No image found in response",
            error_type="empty_response",
            provider="abacus_ai",
            aspect_ratio=aspect,
            model=model_id,
        )

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _extract_image(
        self, data: dict, model_id: str
    ) -> Optional[str]:
        """Extract image from Abacus AI response.

        Abacus AI RouteLLM returns images in OpenAI-compatible format:
        ``choices[0].message.images[].image_url.url`` (data URI).
        """
        try:
            choices = data.get("choices", [])
            if not choices:
                return None

            msg = choices[0].get("message", {})
            images = msg.get("images") or []

            for img in images:
                url = (
                    (img.get("image_url") or {}).get("url")
                    or img.get("url", "")
                )
                if url:
                    if url.startswith("data:image"):
                        ext = detect_image_format(url)
                        raw_b64 = strip_data_url_prefix(url)
                        return str(
                            save_b64_image(
                                raw_b64, prefix=model_id, extension=ext
                            )
                        )
                    return str(
                        save_url_image(url, prefix=model_id)
                    )

            # Fallback: check content field for inline data
            content = msg.get("content", "")
            if content and "data:image" in content:
                import re

                match = re.search(
                    r"data:image/[^;]+;base64,([a-zA-Z0-9+/=]+)",
                    content,
                )
                if match:
                    return str(
                        save_b64_image(
                            match.group(1), prefix=model_id
                        )
                    )

            # Fallback: check inline_data format
            inline_data = msg.get("inline_data") or msg.get(
                "inlineData"
            )
            if isinstance(inline_data, dict):
                b64_data = inline_data.get("data", "")
                if b64_data:
                    return str(
                        save_b64_image(b64_data, prefix=model_id)
                    )
        except Exception as exc:
            logger.debug(
                "Failed to extract image from response: %s", exc
            )

        return None
