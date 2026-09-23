"""Abacus AI image generation provider for Hermes Agent.

Uses Abacus AI's RouteLLM API which provides access to FLUX, DALL-E,
MidJourney, and many other image generation models through a single
OpenAI-compatible endpoint.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def register(ctx: Any) -> None:
    """Register the Abacus AI image gen provider and background tools."""
    # Import provider lazily so tests can import submodules without
    # requiring the full Hermes agent SDK
    from .provider import AbacusAIImageProvider  # noqa: PLC0415

    # Register the image generation provider
    ctx.register_image_gen_provider(AbacusAIImageProvider())

    # Register background generation tool
    # pylint: disable=import-outside-toplevel
    from . import background

    bg_schema = {
        "name": "image_generate_background",
        "description": (
            "Start one or more image generation jobs in the background and "
            "return immediately with a job_id. Use "
            "image_generate_background_status to poll for results. "
            "Supports batch generation via the 'jobs' array."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Describe the image to generate",
                },
                "aspect_ratio": {
                    "type": "string",
                    "enum": ["square", "landscape", "portrait"],
                    "description": "Aspect ratio of the image",
                },
                "model": {
                    "type": "string",
                    "description": "Model override (e.g. flux2_pro, nano_banana_pro)",
                },
                "quality": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Quality tier (OpenAI models)",
                },
                "resolution": {
                    "type": "string",
                    "description": "Resolution: 1080p, 2K, 4K (nano_banana_pro only)",
                },
                "num_images": {
                    "type": "integer",
                    "description": "Number of images (1-4, model dependent)",
                },
                "jobs": {
                    "type": "array",
                    "description": "Batch of generation specs for multiple images",
                    "items": {
                        "type": "object",
                        "properties": {
                            "prompt": {"type": "string"},
                            "aspect_ratio": {
                                "type": "string",
                                "enum": ["square", "landscape", "portrait"],
                            },
                            "model": {"type": "string"},
                            "quality": {
                                "type": "string",
                                "enum": ["low", "medium", "high"],
                            },
                            "resolution": {"type": "string"},
                        },
                    },
                },
            },
        },
    }

    ctx.register_tool(
        name="image_generate_background",
        toolset="abacus_ai",
        schema=bg_schema,
        handler=background.image_generate_background_handler,
        description="Start background image generation jobs",
    )

    bg_status_schema = {
        "name": "image_generate_background_status",
        "description": (
            "Check the status and result of a background image generation job. "
            "Returns the current status and the result if completed."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "Job ID from image_generate_background",
                },
            },
            "required": ["job_id"],
        },
    }

    ctx.register_tool(
        name="image_generate_background_status",
        toolset="abacus_ai",
        schema=bg_status_schema,
        handler=background.image_generate_background_status_handler,
        description="Check background job status",
    )

    logger.info("Plugin 'abacus_ai' registered image_gen provider and background tools")
