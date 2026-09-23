"""Configuration helpers for the Abacus AI image generation provider.

Resolves API credentials and image_gen config from Hermes' config.yaml
and environment variables.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Abacus AI RouteLLM API
ABACUS_AI_DEFAULT_BASE_URL = "https://routellm.abacus.ai/v1"


def load_image_gen_config() -> Dict[str, Any]:
    """Read the ``image_gen`` section from Hermes config.yaml."""
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
        section = cfg.get("image_gen") if isinstance(cfg, dict) else None
        return section if isinstance(section, dict) else {}
    except Exception as exc:
        logger.debug("could not load image_gen config: %s", exc)
        return {}


def resolve_credentials() -> tuple[str, str]:
    """Resolve ``(base_url, api_key)`` for Abacus AI.

    Resolution order:
      1. ``custom_providers`` section in ``config.yaml`` (name: ``abacus-ai``)
      2. ``ABACUS_AI_API_KEY`` / ``ABACUS_AI_BASE_URL`` env vars

    Returns ``(\"\", \"\")`` when no credentials are found.
    """
    # First, try custom_providers section in config.yaml
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
        custom = cfg.get("custom_providers", [])
        if isinstance(custom, list):
            for provider in custom:
                if (
                    isinstance(provider, dict)
                    and provider.get("name") == "abacus-ai"
                ):
                    base_url = (
                        str(
                            provider.get(
                                "base_url", ABACUS_AI_DEFAULT_BASE_URL
                            )
                        )
                        .strip()
                        .rstrip("/")
                    )
                    api_key = str(provider.get("api_key", "")).strip()
                    if api_key:
                        return base_url, api_key
    except Exception:
        pass

    # Fallback: env vars
    import os

    api_key = os.environ.get("ABACUS_AI_API_KEY", "").strip()
    base_url = (
        os.environ.get("ABACUS_AI_BASE_URL", ABACUS_AI_DEFAULT_BASE_URL)
        .strip()
        .rstrip("/")
    )
    if api_key:
        return base_url, api_key
    return ("", "")


def resolve_model_chain(
    explicit: str | None = None,
) -> list[str]:
    """Resolve model chain: explicit -> config -> env -> default."""
    import os

    if isinstance(explicit, str) and explicit.strip():
        return [explicit.strip()]

    env_override = os.environ.get("ABACUS_AI_IMAGE_MODEL", "").strip()
    if env_override:
        return [env_override]

    cfg = load_image_gen_config()
    scoped = (
        cfg.get("abacus_ai") if isinstance(cfg.get("abacus_ai"), dict) else {}
    )
    if isinstance(scoped, dict):
        value = scoped.get("model")
        if isinstance(value, str) and value.strip():
            return [value.strip()]

    top = cfg.get("model")
    if isinstance(top, str) and top.strip():
        return [top.strip()]

    from .models import DEFAULT_MODEL

    return [DEFAULT_MODEL]
