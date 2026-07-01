"""fal-image use-case router.

11 routing chains from Q3 2026 research (fal-ai-landscape + models-summary).
Auto-detects use case from prompt keywords.
Returns primary model (first in chain) for generate_for_use_case etc.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

USE_CASE_CHAINS: Dict[str, List[str]] = {
    "hero_photoreal": ["fal-ai/flux-2-pro", "fal-ai/flux-pro/v1.1-ultra", "fal-ai/bytedance/seedream/v4.5/text-to-image"],
    "logo_text_poster": ["ideogram/v4", "fal-ai/gpt-image-2", "fal-ai/recraft/v4/text-to-image"],
    "vector_svg_icon": ["fal-ai/recraft/v4/text-to-vector", "ideogram/v4", "fal-ai/recraft/v3/text-to-image"],
    "transparent_sticker": ["ideogram/v4", "fal-ai/flux-2-pro", "fal-ai/recraft/v4/text-to-vector"],
    "sketch_draft_quick": ["fal-ai/flux/schnell", "fal-ai/flux/dev", "fal-ai/bytedance/seedream/v5/lite/text-to-image"],
    "social_vertical": ["fal-ai/nano-banana-2", "fal-ai/flux-2-pro", "fal-ai/bytedance/seedream/v4.5/text-to-image"],
    "illustration_anime": ["krea/krea-2", "fal-ai/recraft/v4/text-to-image", "fal-ai/qwen-image-2/text-to-image"],
    "edit_modify": ["fal-ai/flux-2-pro/edit", "fal-ai/nano-banana-2/edit", "fal-ai/gpt-image-2/image-to-image"],
    "upscale": ["fal-ai/clarity-upscaler", "fal-ai/esrgan"],
    "background_removal": ["fal-ai/bria/background/remove", "fal-ai/imageutils/rembg"],
    "complex_text_heavy": ["fal-ai/gpt-image-2", "fal-ai/nano-banana-pro", "fal-ai/qwen-image-2/pro/text-to-image"],
}

USE_CASE_KEYWORDS: Dict[str, List[str]] = {
    "edit_modify": ["edit", "modify", "inpaint", "replace in image", "refine image"],
    "logo_text_poster": ["logo", "text", "poster", "typography", "brand", "wordmark"],
    "vector_svg_icon": ["vector", "svg", "icon", "glyph"],
    "transparent_sticker": ["transparent", "sticker", "alpha", "png alpha", "sticker pack"],
    "sketch_draft_quick": ["sketch", "draft", "quick", "thumbnail", "fast", "rough", "prototype"],
    "social_vertical": ["9:16", "vertical", "story", "instagram", "social", "portrait", "reels", "tiktok"],
    "illustration_anime": ["anime", "illustration", "artistic", "painting", "style", "manga", "cartoon"],
    "upscale": ["upscale", "4k", "enhance", "hd", "high res", "print"],
    "background_removal": ["background", "remove bg", "transparent bg", "cutout", "rmbg"],
    "complex_text_heavy": ["text-heavy", "detailed text", "infographic", "ui", "poster text", "typography heavy", "signage"],
    "hero_photoreal": ["hero", "photoreal", "cinematic", "product", "studio", "realistic", "photo"],
}


def detect_use_case(prompt: str) -> str:
    """Auto-detect best use case from prompt keywords (case-insensitive).
    Check more specific (text-heavy, complex) before generic (logo/poster).
    """
    if not prompt:
        return "hero_photoreal"
    p = prompt.lower()
    # Prioritize specific first (edit before generic bg)
    priority_order = [
        "complex_text_heavy", "edit_modify", "upscale",
        "background_removal", "vector_svg_icon", "transparent_sticker",
        "social_vertical", "illustration_anime", "sketch_draft_quick",
        "logo_text_poster", "hero_photoreal"
    ]
    for uc in priority_order:
        kws = USE_CASE_KEYWORDS.get(uc, [])
        if any(kw in p for kw in kws):
            return uc
    # aspect hints
    if re.search(r"\b9:16\b|vertical|portrait|story", p):
        return "social_vertical"
    if re.search(r"\b16:9\b|landscape|wide|cinematic", p):
        return "hero_photoreal"
    return "hero_photoreal"


def route_use_case(use_case: str, **prefs) -> str:
    """Return primary (recommended first) model_id for the use_case.

    prefs may include prefer_speed=True to pick fast variant from chain.
    """
    chain = USE_CASE_CHAINS.get(use_case, USE_CASE_CHAINS["hero_photoreal"])
    if prefs.get("prefer_speed"):
        for m in chain:
            if any(x in m for x in ["schnell", "lite", "fast"]):
                return m
    return chain[0]


def get_use_case_chain(use_case: str) -> List[str]:
    """Return full fallback chain for use_case (for doctor/route CLI and docs)."""
    return USE_CASE_CHAINS.get(use_case, USE_CASE_CHAINS["hero_photoreal"]).copy()


def list_use_cases() -> List[str]:
    return list(USE_CASE_CHAINS.keys())


# For convenience in client
__all__ = [
    "USE_CASE_CHAINS",
    "detect_use_case",
    "route_use_case",
    "get_use_case_chain",
    "list_use_cases",
]