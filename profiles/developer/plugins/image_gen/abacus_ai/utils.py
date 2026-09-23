"""Utility functions for the Abacus AI image generation provider.

Handles reference image URL conversion and output format detection.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def to_image_url_part(ref: str) -> Optional[str]:
    """Convert a local file path or URL to an inline image URL part.

    Remote URLs pass through unchanged. Local files are read and inlined
    as ``data:`` URIs so the API request is self-contained.
    """
    ref = str(ref or "").strip()
    if not ref:
        return None
    if ref.startswith(("http://", "https://", "data:")):
        return ref

    path = Path(ref)
    if not path.exists():
        logger.debug("reference image not found: %s", ref)
        return None

    try:
        import base64
        import mimetypes

        data = path.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        mime = mimetypes.guess_type(str(path))[0] or "image/png"
        return f"data:{mime};base64,{b64}"
    except Exception as exc:
        logger.debug("failed to inline reference image %s: %s", ref, exc)
        return None


def detect_image_format(data_url: str) -> str:
    """Detect the image format from a ``data:`` URL and return a file extension.

    Examples:
        ``data:image/png;base64,...`` → ``png``
        ``data:image/jpeg;base64,...`` → ``jpg``
        ``data:image/webp;base64,...`` → ``webp``
    """
    import re

    match = re.match(r"data:image/(\w+)", data_url)
    ext = match.group(1) if match else "png"
    return "jpg" if ext == "jpeg" else ext


def strip_data_url_prefix(data_url: str) -> str:
    """Strip the ``data:image/...;base64,`` prefix, returning raw base64."""
    if "base64," in data_url:
        return data_url.split("base64,", 1)[-1]
    return data_url
