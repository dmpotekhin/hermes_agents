"""Background image generation for Abacus AI provider.

Allows running image generation asynchronously — the caller receives a
``job_id`` immediately and can poll for the result later.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _jobs_dir() -> Path:
    """Return the directory where background job state is stored."""
    try:
        from hermes_constants import get_hermes_home
        return get_hermes_home() / "cache" / "abacus_ai_jobs"
    except ImportError:
        return Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))) / "cache" / "abacus_ai_jobs"


def _image_generate_sync(
    prompt: str,
    aspect_ratio: str = "square",
    model: Optional[str] = None,
    quality: Optional[str] = None,
    resolution: Optional[str] = None,
    num_images: Optional[int] = None,
    rewrite_prompt: Optional[bool] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Run a single image generation synchronously and return the result dict.

    This is the worker that background threads call. It imports the provider
    lazily to avoid circular imports at module level.
    """
    # pylint: disable=import-outside-toplevel
    from .provider import AbacusAIImageProvider

    provider = AbacusAIImageProvider()

    # Build kwargs for the provider's generate() method
    gen_kwargs: Dict[str, Any] = dict(kwargs)
    if model:
        gen_kwargs["model"] = model
    if quality:
        gen_kwargs["quality"] = quality
    if resolution:
        gen_kwargs["resolution"] = resolution
    if num_images is not None:
        gen_kwargs["num_images"] = num_images
    if rewrite_prompt is not None:
        gen_kwargs["rewrite_prompt"] = rewrite_prompt

    return provider.generate(
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        **gen_kwargs,
    )


def _run_job(job_id: str, params: Dict[str, Any]) -> None:
    """Run a background job and write the result to disk."""
    jobs_dir = _jobs_dir()
    job_dir = jobs_dir / job_id
    status_path = job_dir / "status.json"
    result_path = job_dir / "result.json"

    # Mark as running
    _write_status(status_path, {"job_id": job_id, "status": "running"})

    try:
        # Determine if this is a single job or a batch
        jobs_list = params.get("jobs")
        if isinstance(jobs_list, list) and len(jobs_list) > 0:
            # Batch mode: run each prompt sequentially
            results = []
            for job_spec in jobs_list:
                if isinstance(job_spec, dict):
                    result = _image_generate_sync(
                        prompt=job_spec.get("prompt", ""),
                        aspect_ratio=job_spec.get(
                            "aspect_ratio", params.get("aspect_ratio", "square")
                        ),
                        model=job_spec.get("model"),
                        quality=job_spec.get("quality"),
                        resolution=job_spec.get("resolution"),
                    )
                    results.append(result)
                else:
                    results.append(
                        {"success": False, "error": "Invalid job spec"}
                    )

            status_msg = "completed" if any(
                r.get("success") for r in results
            ) else "failed"
            _write_status(status_path, {
                "job_id": job_id,
                "status": status_msg,
                "total": len(results),
                "completed": sum(1 for r in results if r.get("success")),
            })
            _write_json(result_path, {"results": results})
        else:
            # Single job mode
            result = _image_generate_sync(
                prompt=params.get("prompt", ""),
                aspect_ratio=params.get("aspect_ratio", "square"),
                model=params.get("model"),
                quality=params.get("quality"),
                resolution=params.get("resolution"),
                num_images=params.get("num_images"),
                rewrite_prompt=params.get("rewrite_prompt"),
            )
            status = "completed" if result.get("success") else "failed"
            _write_status(status_path, {
                "job_id": job_id,
                "status": status,
                "success": result.get("success", False),
            })
            _write_json(result_path, result)

    except Exception as exc:
        logger.error("Background job %s failed: %s", job_id, exc)
        _write_status(status_path, {
            "job_id": job_id,
            "status": "failed",
            "error": str(exc),
        })


def _write_status(path: Path, data: Dict[str, Any]) -> None:
    """Write status JSON to disk atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def _write_json(path: Path, data: Any) -> None:
    """Write result JSON to disk atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


# ------------------------------------------------------------------
# Tool handlers
# ------------------------------------------------------------------


def image_generate_background_handler(
    args: dict, **kwargs: Any
) -> str:
    """Start a background image generation job.

    Accepts the same parameters as ``image_generate`` plus an optional
    ``jobs`` array for batch generation. Returns immediately with a
    ``job_id``. Use ``image_generate_background_status`` to poll for
    completion.

    Parameters in ``args``:
        prompt (str): The image description.
        aspect_ratio (str, optional): ``square``, ``landscape``, or
            ``portrait``. Default ``square``.
        model (str, optional): Model ID override.
        quality (str, optional): ``low``, ``medium``, ``high``.
        resolution (str, optional): ``1080p``, ``2K``, ``4K``.
        num_images (int, optional): 1-4 images.
        rewrite_prompt (bool, optional): Auto-improve prompt.
        jobs (list, optional): Batch of job specs, each with its own
            ``prompt`` and optional overrides.
    """
    prompt = (args.get("prompt") or "").strip()
    if not prompt and not args.get("jobs"):
        return json.dumps({
            "success": False,
            "error": "Prompt is required",
            "purpose": "background_job_creation",
        })

    job_id = uuid.uuid4().hex[:12]

    # Spawn worker thread
    params = dict(args)
    thread = threading.Thread(
        target=_run_job,
        args=(job_id, params),
        daemon=True,
        name=f"abacus-ai-bg-{job_id}",
    )
    thread.start()

    return json.dumps({
        "success": True,
        "job_id": job_id,
        "status": "queued",
        "purpose": "background_job_creation",
    })


def image_generate_background_status_handler(
    args: dict, **kwargs: Any
) -> str:
    """Check the status of a background image generation job.

    Parameters in ``args``:
        job_id (str): The job ID returned by
            ``image_generate_background``.
    """
    job_id = (args.get("job_id") or "").strip()
    if not job_id:
        return json.dumps({
            "success": False,
            "error": "job_id is required",
        })

    job_dir = _jobs_dir() / job_id
    status_path = job_dir / "status.json"
    result_path = job_dir / "result.json"

    if not status_path.exists():
        return json.dumps({
            "success": False,
            "error": f"Job '{job_id}' not found",
        })

    try:
        status = json.loads(status_path.read_text(encoding="utf-8"))
        result = None
        if result_path.exists():
            result = json.loads(result_path.read_text(encoding="utf-8"))
        return json.dumps({
            "success": True,
            "job_id": job_id,
            "status": status.get("status", "unknown"),
            "result": result,
        })
    except Exception as exc:
        return json.dumps({
            "success": False,
            "error": str(exc),
        })
