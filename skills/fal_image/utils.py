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


# Cost estimation backed by registry data (Q3 2026)
from .registry import get_model  # type: ignore  # circular safe at runtime

def estimate_cost(model_id: str, num_images: int = 1, aspect: str = "1:1") -> float:
    """Better USD estimate using registry prices (or conservative default)."""
    info = get_model(model_id)
    if info:
        per = info.cost_per_image_usd
    else:
        tier_cost = {
            "fal-ai/flux/schnell": 0.003,
            "fal-ai/flux/dev": 0.025,
            "fal-ai/flux-2-pro": 0.03,
            "fal-ai/flux-pro/v1.1-ultra": 0.06,
            "ideogram/v4": 0.03,
            "fal-ai/recraft/v4/text-to-vector": 0.08,
        }
        per = tier_cost.get(model_id, 0.03)
    # crude aspect multiplier (research: size matters)
    mult = 1.0
    if "16:9" in aspect or "landscape" in aspect.lower():
        mult = 1.2
    elif "9:16" in aspect or "portrait" in aspect.lower():
        mult = 1.1
    return round(per * num_images * mult, 4)


def get_model_cost(model_id: str) -> float:
    info = get_model(model_id)
    return info.cost_per_image_usd if info else 0.03