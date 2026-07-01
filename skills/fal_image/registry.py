"""fal-image model registry.

Single source of truth for supported fal.ai image models and their capabilities.
Update this file when adding or changing models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional, List


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
    # NEW fields from Q3 2026 research
    use_cases: List[str] = field(default_factory=list)
    cost_per_image_usd: float = 0.03
    latency_seconds: str = "5-15"
    fal_endpoint: Optional[str] = None  # if differs from model_id


# Authoritative registry — keep this complete and up-to-date.
# Populated from memory/research/fal-ai-models-summary.json + landscape (Q3 2026).
# 24+ models, with use_cases, cost, latency.
MODEL_REGISTRY: dict[str, ModelInfo] = {
    # --- Existing + updated FLUX family ---
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
        use_cases=["sketch_draft_quick"],
        cost_per_image_usd=0.003,
        latency_seconds="1-2",
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
        use_cases=["sketch_draft_quick", "hero_photoreal"],
        cost_per_image_usd=0.025,
        latency_seconds="2-5",
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
        use_cases=["hero_photoreal"],
        cost_per_image_usd=0.06,
        latency_seconds="10-20",
    ),
    "fal-ai/flux-2-pro": ModelInfo(
        model_id="fal-ai/flux-2-pro",
        display_name="FLUX.2 [pro]",
        family="flux-2",
        tier="premium",
        supports_text_to_image=True,
        supports_image_to_image=True,
        supports_edit=True,
        max_reference_images=9,
        supports_aspect_ratio=True,
        supports_raw=True,
        safety_param="enable_safety_checker",
        notes="New top all-rounder: studio-grade photorealism, zero-config, JSON/HEX support, multi-ref. Primary recommendation.",
        use_cases=["hero_photoreal", "transparent_sticker", "social_vertical"],
        cost_per_image_usd=0.03,
        latency_seconds="5-15",
    ),
    "fal-ai/flux-2-pro/edit": ModelInfo(
        model_id="fal-ai/flux-2-pro/edit",
        display_name="FLUX.2 [pro] Edit",
        family="flux-2",
        tier="premium",
        supports_text_to_image=False,
        supports_image_to_image=True,
        supports_edit=True,
        max_reference_images=9,
        supports_aspect_ratio=True,
        safety_param="enable_safety_checker",
        notes="Production compositing and multi-reference editing.",
        use_cases=["edit_modify"],
        cost_per_image_usd=0.03,
        latency_seconds="5-15",
    ),
    "fal-ai/flux-pro/kontext": ModelInfo(
        model_id="fal-ai/flux-pro/kontext",
        display_name="FLUX.1 Kontext [pro]",
        family="kontext",
        tier="premium",
        supports_text_to_image=False,
        supports_image_to_image=True,
        supports_edit=True,
        max_reference_images=2,
        supports_aspect_ratio=True,
        safety_param="safety_tolerance",
        notes="Character consistency, multi-turn edits, text changes in images.",
        use_cases=["edit_modify"],
        cost_per_image_usd=0.04,
        latency_seconds="10-20",
    ),
    "fal-ai/flux-pro/kontext/max": ModelInfo(
        model_id="fal-ai/flux-pro/kontext/max",
        display_name="FLUX.1 Kontext [max]",
        family="kontext",
        tier="premium",
        supports_text_to_image=False,
        supports_image_to_image=True,
        supports_edit=True,
        max_reference_images=2,
        supports_aspect_ratio=True,
        safety_param="safety_tolerance",
        notes="Premium consistency and typography for edits.",
        use_cases=["edit_modify"],
        cost_per_image_usd=0.06,
        latency_seconds="10-20",
    ),
    # --- Nano Banana / Google ---
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
        notes="Excellent multi-reference editor. Great for character consistency. Good for social/vertical.",
        use_cases=["social_vertical", "edit_modify"],
        cost_per_image_usd=0.08,
        latency_seconds="5-15",
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
        use_cases=["edit_modify"],
        cost_per_image_usd=0.08,
        latency_seconds="5-15",
    ),
    "fal-ai/nano-banana-pro": ModelInfo(
        model_id="fal-ai/nano-banana-pro",
        display_name="Nano Banana Pro",
        family="nano-banana",
        tier="premium",
        supports_text_to_image=True,
        supports_image_to_image=True,
        supports_edit=True,
        max_reference_images=14,
        supports_aspect_ratio=True,
        safety_param="safety_tolerance",
        notes="Best-in-class reasoning, premium text. Expensive.",
        use_cases=["complex_text_heavy"],
        cost_per_image_usd=0.15,
        latency_seconds="15-30",
    ),
    # --- Ideogram (text / transparent king) ---
    "ideogram/v4": ModelInfo(
        model_id="ideogram/v4",
        display_name="Ideogram v4",
        family="ideogram",
        tier="balanced",
        supports_text_to_image=True,
        supports_image_to_image=False,
        max_reference_images=0,
        supports_aspect_ratio=True,
        safety_param="enable_safety_checker",
        notes="Best-in-class text rendering, logos, native transparency. Tiered pricing.",
        use_cases=["logo_text_poster", "transparent_sticker", "vector_svg_icon"],
        cost_per_image_usd=0.03,
        latency_seconds="3-15",
    ),
    # --- Recraft (vector / design) ---
    "fal-ai/recraft/v4/text-to-image": ModelInfo(
        model_id="fal-ai/recraft/v4/text-to-image",
        display_name="Recraft V4",
        family="recraft",
        tier="balanced",
        supports_text_to_image=True,
        supports_image_to_image=False,
        max_reference_images=0,
        supports_aspect_ratio=True,
        safety_param=None,
        notes="Design-grade, brand-system rendering. Good for volume.",
        use_cases=["logo_text_poster", "illustration_anime"],
        cost_per_image_usd=0.04,
        latency_seconds="3-10",
    ),
    "fal-ai/recraft/v4/text-to-vector": ModelInfo(
        model_id="fal-ai/recraft/v4/text-to-vector",
        display_name="Recraft V4 Vector",
        family="recraft",
        tier="balanced",
        supports_text_to_image=True,
        supports_image_to_image=False,
        max_reference_images=0,
        supports_aspect_ratio=False,
        safety_param=None,
        notes="Native SVG output. Vector/SVG specialist.",
        use_cases=["vector_svg_icon", "transparent_sticker"],
        cost_per_image_usd=0.08,
        latency_seconds="5-15",
    ),
    "fal-ai/recraft/v4/pro/text-to-image": ModelInfo(
        model_id="fal-ai/recraft/v4/pro/text-to-image",
        display_name="Recraft V4 Pro",
        family="recraft",
        tier="premium",
        supports_text_to_image=True,
        supports_image_to_image=False,
        max_reference_images=0,
        supports_aspect_ratio=True,
        safety_param=None,
        notes="Premium design quality, 2K native.",
        use_cases=["logo_text_poster"],
        cost_per_image_usd=0.25,
        latency_seconds="10-20",
    ),
    "fal-ai/recraft/v4/pro/text-to-vector": ModelInfo(
        model_id="fal-ai/recraft/v4/pro/text-to-vector",
        display_name="Recraft V4 Pro Vector",
        family="recraft",
        tier="premium",
        supports_text_to_image=True,
        supports_image_to_image=False,
        max_reference_images=0,
        supports_aspect_ratio=False,
        safety_param=None,
        notes="Premium SVG, brand systems.",
        use_cases=["vector_svg_icon"],
        cost_per_image_usd=0.30,
        latency_seconds="10-20",
    ),
    "fal-ai/recraft/v3/text-to-image": ModelInfo(
        model_id="fal-ai/recraft/v3/text-to-image",
        display_name="Recraft V3",
        family="recraft",
        tier="balanced",
        supports_text_to_image=True,
        supports_image_to_image=False,
        max_reference_images=0,
        supports_aspect_ratio=True,
        safety_param=None,
        notes="HF Arena winner (ELO 1172). Fallback vector/raster.",
        use_cases=["vector_svg_icon"],
        cost_per_image_usd=0.04,
        latency_seconds="3-10",
    ),
    # --- Seedream (ByteDance) ---
    "fal-ai/bytedance/seedream/v4.5/text-to-image": ModelInfo(
        model_id="fal-ai/bytedance/seedream/v4.5/text-to-image",
        display_name="Seedream 4.5",
        family="seedream",
        tier="balanced",
        supports_text_to_image=True,
        supports_image_to_image=True,
        supports_edit=True,
        max_reference_images=0,
        supports_aspect_ratio=True,
        safety_param=None,
        notes="Photoreal, unified gen+edit, strong adherence.",
        use_cases=["hero_photoreal", "social_vertical"],
        cost_per_image_usd=0.04,
        latency_seconds="10-30",
    ),
    "fal-ai/bytedance/seedream/v5/lite/text-to-image": ModelInfo(
        model_id="fal-ai/bytedance/seedream/v5/lite/text-to-image",
        display_name="Seedream 5.0 Lite",
        family="seedream",
        tier="fast",
        supports_text_to_image=True,
        supports_image_to_image=True,
        supports_edit=True,
        max_reference_images=0,
        supports_aspect_ratio=True,
        safety_param=None,
        notes="Web retrieval, reasoning, fast lite version.",
        use_cases=["sketch_draft_quick"],
        cost_per_image_usd=0.035,
        latency_seconds="8-20",
    ),
    # --- Qwen ---
    "fal-ai/qwen-image-2/text-to-image": ModelInfo(
        model_id="fal-ai/qwen-image-2/text-to-image",
        display_name="Qwen Image 2.0",
        family="qwen",
        tier="balanced",
        supports_text_to_image=True,
        supports_image_to_image=True,
        supports_edit=True,
        max_reference_images=0,
        supports_aspect_ratio=True,
        safety_param=None,
        notes="Native 2K, good text/value for infographics.",
        use_cases=["illustration_anime", "complex_text_heavy"],
        cost_per_image_usd=0.035,
        latency_seconds="5-15",
    ),
    "fal-ai/qwen-image-2/pro/text-to-image": ModelInfo(
        model_id="fal-ai/qwen-image-2/pro/text-to-image",
        display_name="Qwen Image 2.0 Pro",
        family="qwen",
        tier="premium",
        supports_text_to_image=True,
        supports_image_to_image=True,
        supports_edit=True,
        max_reference_images=0,
        supports_aspect_ratio=True,
        safety_param=None,
        notes="Professional typography, comics, infographics.",
        use_cases=["complex_text_heavy"],
        cost_per_image_usd=0.075,
        latency_seconds="10-20",
    ),
    # --- GPT Image ---
    "fal-ai/gpt-image-2": ModelInfo(
        model_id="fal-ai/gpt-image-2",
        display_name="GPT Image 2",
        family="gpt-image",
        tier="premium",
        supports_text_to_image=True,
        supports_image_to_image=True,
        supports_edit=True,
        max_reference_images=1,
        supports_aspect_ratio=True,
        safety_param=None,
        notes="Near-perfect text, extreme prompt adherence. Tiered quality (low/medium/high).",
        use_cases=["logo_text_poster", "complex_text_heavy", "edit_modify"],
        cost_per_image_usd=0.04,
        latency_seconds="15-60",
    ),
    "fal-ai/gpt-image-2/image-to-image": ModelInfo(
        model_id="fal-ai/gpt-image-2/image-to-image",
        display_name="GPT Image 2 (Edit)",
        family="gpt-image",
        tier="premium",
        supports_text_to_image=False,
        supports_image_to_image=True,
        supports_edit=True,
        max_reference_images=1,
        supports_aspect_ratio=True,
        safety_param=None,
        notes="Mask-based inpainting, extreme adherence.",
        use_cases=["edit_modify"],
        cost_per_image_usd=0.04,
        latency_seconds="15-60",
    ),
    # --- Krea (artistic) ---
    "krea/krea-2": ModelInfo(
        model_id="krea/krea-2",
        display_name="Krea 2",
        family="krea",
        tier="balanced",
        supports_text_to_image=True,
        supports_image_to_image=False,
        max_reference_images=10,
        supports_aspect_ratio=True,
        safety_param=None,
        notes="Illustration, anime, painting, expressive styles (May 2026 launch). Medium/Pro variants.",
        use_cases=["illustration_anime"],
        cost_per_image_usd=0.03,
        latency_seconds="3-10",
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
        safety_param=None,
        notes="High creativity. Supports multiple style references (legacy alias).",
        use_cases=["illustration_anime"],
        cost_per_image_usd=0.03,
        latency_seconds="3-10",
    ),
    # --- Upscale ---
    "fal-ai/clarity-upscaler": ModelInfo(
        model_id="fal-ai/clarity-upscaler",
        display_name="Clarity Upscaler",
        family="upscale",
        tier="balanced",
        supports_text_to_image=False,
        supports_image_to_image=True,
        supports_edit=False,
        max_reference_images=0,
        supports_aspect_ratio=False,
        safety_param=None,
        notes="High fidelity AI upscaler.",
        use_cases=["upscale"],
        cost_per_image_usd=0.01,
        latency_seconds="2-5",
    ),
    "fal-ai/esrgan": ModelInfo(
        model_id="fal-ai/esrgan",
        display_name="ESRGAN",
        family="upscale",
        tier="fast",
        supports_text_to_image=False,
        supports_image_to_image=True,
        supports_edit=False,
        max_reference_images=0,
        supports_aspect_ratio=False,
        safety_param=None,
        notes="Classic 4x super-resolution, cheap.",
        use_cases=["upscale"],
        cost_per_image_usd=0.005,
        latency_seconds="1-3",
    ),
    # --- Background removal ---
    "fal-ai/bria/background/remove": ModelInfo(
        model_id="fal-ai/bria/background/remove",
        display_name="Bria RMBG 2.0",
        family="bg-removal",
        tier="balanced",
        supports_text_to_image=False,
        supports_image_to_image=True,
        supports_edit=False,
        max_reference_images=0,
        supports_aspect_ratio=False,
        safety_param=None,
        notes="State-of-the-art licensed background removal, alpha output.",
        use_cases=["background_removal", "transparent_sticker"],
        cost_per_image_usd=0.018,
        latency_seconds="1-3",
    ),
    "fal-ai/imageutils/rembg": ModelInfo(
        model_id="fal-ai/imageutils/rembg",
        display_name="RMBG (Generic)",
        family="imageutils",
        tier="fast",
        supports_text_to_image=False,
        supports_image_to_image=True,
        supports_edit=False,
        max_reference_images=0,
        supports_aspect_ratio=False,
        safety_param=None,
        notes="Basic/cheap background removal fallback.",
        use_cases=["background_removal"],
        cost_per_image_usd=0.001,
        latency_seconds="1-2",
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
    use_case: Optional[str] = None,
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
    if use_case:
        results = [m for m in results if use_case in (m.use_cases or [])]

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


# Convenience constants (updated per Q3 2026 research)
DEFAULT_MODEL = "fal-ai/flux-2-pro"
FAST_MODEL = "fal-ai/flux/schnell"
PREMIUM_MODEL = "fal-ai/flux-2-pro"
BEST_EDITOR = "fal-ai/flux-2-pro/edit"


def get_all_model_ids() -> list[str]:
    """Return all registered model IDs."""
    return list(MODEL_REGISTRY.keys())


if __name__ == "__main__":
    print("Registered models (count={}):".format(len(MODEL_REGISTRY)))
    for mid, info in MODEL_REGISTRY.items():
        print(f"  {mid:40} | {info.display_name:28} | tier={info.tier:8} | cost=${info.cost_per_image_usd:.3f} | refs={info.max_reference_images}")
    print()
    print("Default primary:", DEFAULT_MODEL)
    print("Best editor:", choose_model(needs_edit=True, max_refs=4))
    print("Fast cheap:", choose_model(prefer_speed=True, budget="low"))
    print("Total models:", len(get_all_model_ids()))