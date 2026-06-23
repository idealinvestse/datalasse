"""fal-image model registry.

Single source of truth for supported fal.ai image models and their capabilities.
Update this file when adding or changing models.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class ModelInfo:
    model_id: str
    display_name: str
    family: str
    tier: Literal["fast", "balanced", "premium"]
    supports_text_to_image: bool = True
    supports_image_to_image: bool = False
    supports_edit: bool = False
    max_reference_images: int = 0
    supports_aspect_ratio: bool = True
    supports_raw: bool = False
    safety_param: Optional[str] = None          # "enable_safety_checker" | "safety_tolerance" | None
    notes: str = ""


# Authoritative registry — keep this complete and up-to-date.
MODEL_REGISTRY: dict[str, ModelInfo] = {
    "fal-ai/flux/schnell": ModelInfo(
        model_id="fal-ai/flux/schnell",
        display_name="Flux Schnell",
        family="flux",
        tier="fast",
        supports_text_to_image=True,
        supports_image_to_image=False,
        max_reference_images=0,
        supports_aspect_ratio=True,
        safety_param="enable_safety_checker",
        notes="Fastest and cheapest. Great for iteration.",
    ),
    "fal-ai/flux/dev": ModelInfo(
        model_id="fal-ai/flux/dev",
        display_name="Flux Dev",
        family="flux",
        tier="balanced",
        supports_text_to_image=True,
        supports_image_to_image=True,
        supports_edit=True,
        max_reference_images=1,
        supports_aspect_ratio=True,
        safety_param="enable_safety_checker",
        notes="Balanced quality/speed. Good default for most work.",
    ),
    "fal-ai/flux-pro/v1.1-ultra": ModelInfo(
        model_id="fal-ai/flux-pro/v1.1-ultra",
        display_name="Flux Pro 1.1 Ultra",
        family="flux",
        tier="premium",
        supports_text_to_image=True,
        supports_image_to_image=True,
        supports_edit=True,
        max_reference_images=1,
        supports_aspect_ratio=True,
        supports_raw=True,
        safety_param="safety_tolerance",
        notes="Highest quality. Use when photorealism or detail matters most.",
    ),
    "fal-ai/nano-banana-2": ModelInfo(
        model_id="fal-ai/nano-banana-2",
        display_name="Nano Banana 2",
        family="nano-banana",
        tier="balanced",
        supports_text_to_image=True,
        supports_image_to_image=True,
        supports_edit=True,
        max_reference_images=14,
        supports_aspect_ratio=True,
        safety_param="safety_tolerance",
        notes="Excellent multi-reference editor. Great for character consistency.",
    ),
    "fal-ai/nano-banana-2/edit": ModelInfo(
        model_id="fal-ai/nano-banana-2/edit",
        display_name="Nano Banana 2 (Edit)",
        family="nano-banana",
        tier="balanced",
        supports_text_to_image=False,
        supports_image_to_image=True,
        supports_edit=True,
        max_reference_images=14,
        supports_aspect_ratio=True,
        safety_param="safety_tolerance",
        notes="Dedicated edit endpoint for Nano Banana.",
    ),
    "fal-ai/ideogram/v4": ModelInfo(
        model_id="fal-ai/ideogram/v4",
        display_name="Ideogram v4",
        family="ideogram",
        tier="balanced",
        supports_text_to_image=True,
        supports_image_to_image=False,
        max_reference_images=0,
        supports_aspect_ratio=True,
        safety_param="enable_safety_checker",
        notes="Strong typography and prompt adherence.",
    ),
    "fal/krea/v2/large/text-to-image": ModelInfo(
        model_id="fal/krea/v2/large/text-to-image",
        display_name="Krea v2 Large",
        family="krea",
        tier="balanced",
        supports_text_to_image=True,
        supports_image_to_image=False,
        max_reference_images=10,
        supports_aspect_ratio=True,
        safety_param=None,  # provider-controlled
        notes="High creativity. Supports multiple style references.",
    ),
}


def get_model(model_id: str) -> Optional[ModelInfo]:
    """Return ModelInfo for a given model_id, or None if unknown."""
    return MODEL_REGISTRY.get(model_id)


def list_models(
    *,
    feature: Optional[str] = None,
    tier: Optional[str] = None,
    family: Optional[str] = None,
) -> list[ModelInfo]:
    """Filter and list models by capability."""
    results = list(MODEL_REGISTRY.values())

    if feature == "edit":
        results = [m for m in results if m.supports_edit]
    elif feature == "i2i":
        results = [m for m in results if m.supports_image_to_image]
    elif feature == "multi_ref":
        results = [m for m in results if m.max_reference_images >= 2]

    if tier:
        results = [m for m in results if m.tier == tier]
    if family:
        results = [m for m in results if m.family == family]

    return results


def choose_model(
    *,
    prefer_quality: bool = False,
    prefer_speed: bool = False,
    needs_edit: bool = False,
    max_refs: int = 0,
    budget: Literal["low", "medium", "high"] = "medium",
) -> str:
    """Simple heuristic model router.

    Returns the model_id of the best match.
    """
    candidates = list_models()

    if needs_edit:
        candidates = [m for m in candidates if m.supports_edit and m.max_reference_images >= max_refs]

    if budget == "low":
        candidates = [m for m in candidates if m.tier == "fast"]
    elif budget == "high" and prefer_quality:
        candidates = [m for m in candidates if m.tier == "premium"]

    if not candidates:
        return "fal-ai/flux/dev"

    # Prefer faster when speed is requested
    if prefer_speed:
        fast = [m for m in candidates if m.tier == "fast"]
        if fast:
            return fast[0].model_id

    # Prefer premium when quality is requested
    if prefer_quality:
        premium = [m for m in candidates if m.tier == "premium"]
        if premium:
            return premium[0].model_id

    # Default: balanced
    balanced = [m for m in candidates if m.tier == "balanced"]
    if balanced:
        return balanced[0].model_id

    return candidates[0].model_id


# Convenience constants
DEFAULT_MODEL = "fal-ai/flux/dev"
FAST_MODEL = "fal-ai/flux/schnell"
PREMIUM_MODEL = "fal-ai/flux-pro/v1.1-ultra"
BEST_EDITOR = "fal-ai/nano-banana-2"


if __name__ == "__main__":
    print("Registered models:")
    for mid, info in MODEL_REGISTRY.items():
        print(f"  {mid:35} | {info.display_name:25} | tier={info.tier:8} | refs={info.max_reference_images}")
    print()
    print("Best editor:", choose_model(needs_edit=True, max_refs=4))
    print("Fast cheap:", choose_model(prefer_speed=True, budget="low"))