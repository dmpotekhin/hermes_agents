"""Model catalog and aspect ratio resolution for Abacus AI image generation.

Defines the supported model catalog, model-specific aspect ratio formats,
and resolution helpers.
"""

from __future__ import annotations

from typing import Any, Dict, List

try:
    from agent.image_gen_provider import resolve_aspect_ratio
except ImportError:
    def resolve_aspect_ratio(r: str) -> str: return r

# ---------------------------------------------------------------------------
# Model-specific aspect ratio formats
# ---------------------------------------------------------------------------

# FLUX models use preset names
_FLUX_ASPECT_RATIOS = {
    "square": "square_hd",
    "landscape": "landscape_16_9",
    "portrait": "portrait_16_9",
}

# MidJourney / DALL-E / FLUX Pro Ultra use simple ratio strings
_STANDARD_ASPECT_RATIOS = {
    "square": "1:1",
    "landscape": "16:9",
    "portrait": "9:16",
}

# Models that use standard ratio strings (1:1, 16:9, etc.)
_STANDARD_ASPECT_MODELS = {"midjourney", "dalle", "flux_pro_ultra", "seedream"}

_REQUEST_TIMEOUT = 300.0

DEFAULT_MODEL = "flux2_pro"

# ---------------------------------------------------------------------------
# Model catalog
# ---------------------------------------------------------------------------

MODEL_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "nano_banana_pro",
        "display": "Nano Banana Pro",
        "strengths": "Highest resolution (up to 4K), Google DeepMind",
    },
    {
        "id": "flux_pro_ultra",
        "display": "FLUX Pro Ultra",
        "strengths": "Highest quality, photorealistic",
    },
    {
        "id": "flux2_pro",
        "display": "FLUX 2 Pro",
        "strengths": "High quality, photorealistic (default)",
    },
    {
        "id": "flux2",
        "display": "FLUX 2",
        "strengths": "Fast, good quality",
    },
    {
        "id": "midjourney",
        "display": "MidJourney",
        "strengths": "Artistic, stylistic generations",
    },
    {
        "id": "dalle",
        "display": "DALL-E",
        "strengths": "Creative, strong prompt adherence",
    },
]


def resolve_aspect_ratio_for_model(
    aspect_ratio: str, model_id: str
) -> str:
    """Resolve the aspect ratio string for a specific model.

    Different models use different aspect ratio formats:

    * FLUX models: ``square_hd``, ``landscape_16_9``, ``portrait_16_9``
    * MidJourney / DALL-E / FLUX Pro Ultra: ``1:1``, ``16:9``, ``9:16``
    """
    aspect = resolve_aspect_ratio(aspect_ratio)

    # Check if this model uses standard ratio format
    model_key = model_id.lower().replace("_", "").replace("-", "")
    for std_model in _STANDARD_ASPECT_MODELS:
        if std_model.replace("_", "") in model_key:
            return _STANDARD_ASPECT_RATIOS.get(aspect, "1:1")

    # Default to FLUX format (covers flux2, flux2_pro, and most others)
    return _FLUX_ASPECT_RATIOS.get(aspect, "square_hd")
