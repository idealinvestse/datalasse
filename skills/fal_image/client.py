"""fal-image client.

High-level generation and editing wrappers that enforce safety-off and use the registry.
"""

from __future__ import annotations

from typing import Any

import fal_client

from .registry import (
    DEFAULT_MODEL,
    BEST_EDITOR,
    get_model,
    choose_model,
)
from .safety import with_safety_off


def generate(
    prompt: str,
    model: str | None = None,
    *,
    aspect_ratio: str = "16:9",
    raw: bool = False,
    num_images: int = 1,
    **extra_kwargs: Any,
) -> dict:
    """Generate an image from text.

    Safety-off is automatically applied.
    """
    model_id = model or DEFAULT_MODEL
    info = get_model(model_id)

    # Smart defaults based on registry
    args: dict[str, Any] = {
        "prompt": prompt,
        "num_images": num_images,
    }

    if info and info.supports_aspect_ratio:
        args["aspect_ratio"] = aspect_ratio

    if raw and info and info.supports_raw:
        args["raw"] = True

    args.update(extra_kwargs)

    safe_args = with_safety_off(model_id, args)
    return fal_client.subscribe(model_id, arguments=safe_args, with_logs=True)


def edit(
    image_url: str,
    prompt: str,
    model: str | None = None,
    *,
    strength: float = 0.7,
    aspect_ratio: str = "16:9",
    num_images: int = 1,
    **extra_kwargs: Any,
) -> dict:
    """Edit an existing image using a prompt (image-to-image / instruct edit).

    Accepts either a fal CDN URL or a local file path (auto-uploaded).
    """
    # Auto-upload if local path is given
    if not image_url.startswith(("http://", "https://", "fal://")):
        image_url = fal_client.upload_file(image_url)

    model_id = model or BEST_EDITOR
    info = get_model(model_id)

    args: dict[str, Any] = {
        "prompt": prompt,
        "image_url": image_url,
        "strength": strength,
        "num_images": num_images,
    }

    if info and info.supports_aspect_ratio:
        args["aspect_ratio"] = aspect_ratio

    args.update(extra_kwargs)

    safe_args = with_safety_off(model_id, args)
    return fal_client.subscribe(model_id, arguments=safe_args, with_logs=True)


def variations(
    image_url: str,
    n: int = 4,
    model: str | None = None,
    *,
    strength: float = 0.55,
    prompt: str | None = None,
    **extra_kwargs: Any,
) -> list[dict]:
    """Create N variations of a reference image.

    Returns list of results (one per variation job).
    """
    if not image_url.startswith(("http://", "https://")):
        image_url = fal_client.upload_file(image_url)

    model_id = model or BEST_EDITOR
    results = []

    for i in range(n):
        args = {
            "image_url": image_url,
            "strength": strength,
            "num_images": 1,
        }
        if prompt:
            args["prompt"] = prompt
        args.update(extra_kwargs)

        safe_args = with_safety_off(model_id, args)
        res = fal_client.subscribe(model_id, arguments=safe_args, with_logs=False)
        results.append(res)

    return results


def choose_and_generate(
    prompt: str,
    *,
    prefer_quality: bool = False,
    prefer_speed: bool = False,
    budget: str = "medium",
    **kwargs: Any,
) -> dict:
    """Convenience: let the router pick the model then generate."""
    model_id = choose_model(
        prefer_quality=prefer_quality,
        prefer_speed=prefer_speed,
        budget=budget,  # type: ignore[arg-type]
    )
    return generate(prompt, model=model_id, **kwargs)


__all__ = ["generate", "edit", "variations", "choose_and_generate"]