"""Utility helpers for fal-image (upload, aspect ratio, cost stubs, etc.)."""

from __future__ import annotations

import fal_client


def upload_image(path_or_url: str) -> str:
    """Upload a local file to fal CDN if needed. Returns a usable URL."""
    if path_or_url.startswith(("http://", "https://", "fal://")):
        return path_or_url
    return fal_client.upload_file(path_or_url)


def normalize_aspect_ratio(ratio: str) -> str:
    """Very small helper to normalize common aspect ratio inputs."""
    mapping = {
        "16:9": "16:9",
        "9:16": "9:16",
        "4:3": "4:3",
        "3:4": "3:4",
        "1:1": "1:1",
        "landscape": "16:9",
        "portrait": "9:16",
        "square": "1:1",
    }
    return mapping.get(ratio.lower(), ratio)


# Placeholder for future cost estimation
def estimate_cost(model_id: str, num_images: int = 1) -> float:
    """Rough USD estimate — update with real pricing later."""
    tier_cost = {
        "fal-ai/flux/schnell": 0.003,
        "fal-ai/flux/dev": 0.012,
        "fal-ai/flux-pro/v1.1-ultra": 0.045,
        "fal-ai/nano-banana-2": 0.025,
    }
    per_image = tier_cost.get(model_id, 0.015)
    return round(per_image * num_images, 4)