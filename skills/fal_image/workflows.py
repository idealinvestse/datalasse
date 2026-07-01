"""fal-image multi-step workflows.

Return WorkflowResult with primary_url, alt urls, aggregated cost/latency, models_used.
Use previous step outputs (image URLs) for chaining where possible.
All respect safety-off via the client functions.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any

from .client import generate, edit, upscale as upscale_fn, remove_background as remove_bg_fn
from .router import route_use_case
from .registry import get_model


@dataclass
class WorkflowResult:
    output_urls: List[str]
    primary_url: str
    total_cost_usd: float
    total_latency_ms: int
    models_used: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


def _estimate_cost(model_id: str, num: int = 1) -> float:
    info = get_model(model_id)
    if info:
        return round(info.cost_per_image_usd * num, 4)
    # conservative fallback
    return round(0.03 * num, 4)


def sketch_to_hero(prompt: str, **kwargs) -> WorkflowResult:
    """schnell (draft) → flux-2-pro (refine) → clarity-upscaler."""
    t0 = time.time()
    models_used: List[str] = []
    costs = 0.0
    urls: List[str] = []

    # 1. Fast draft
    m1 = "fal-ai/flux/schnell"
    draft = generate(prompt, model=m1, num_images=1, **kwargs)
    draft_url = draft["images"][0]["url"]
    urls.append(draft_url)
    models_used.append(m1)
    costs += _estimate_cost(m1)

    # 2. Refine with reference (flux-2-pro supports image_url in practice)
    m2 = "fal-ai/flux-2-pro"
    refine = generate(
        prompt,
        model=m2,
        image_url=draft_url,  # may be treated as reference by model
        num_images=1,
        **kwargs
    )
    refine_url = refine["images"][0]["url"]
    urls.append(refine_url)
    models_used.append(m2)
    costs += _estimate_cost(m2)

    # 3. Upscale
    m3 = "fal-ai/clarity-upscaler"
    up = upscale_fn(refine_url, scale=2)
    up_url = up.get("images", [{}])[0].get("url", refine_url) if isinstance(up, dict) else refine_url
    urls.append(up_url)
    models_used.append(m3)
    costs += _estimate_cost(m3)

    latency = int((time.time() - t0) * 1000)
    return WorkflowResult(
        output_urls=urls,
        primary_url=up_url,
        total_cost_usd=round(costs, 4),
        total_latency_ms=latency,
        models_used=models_used,
        metadata={"steps": 3, "prompt": prompt},
    )


def transparent_sticker(prompt: str, **kwargs) -> WorkflowResult:
    """ideogram/v4 (native alpha) + optional upscale."""
    t0 = time.time()
    m = "ideogram/v4"
    res = generate(prompt, model=m, num_images=1, **kwargs)
    url = res["images"][0]["url"]
    models_used = [m]
    cost = _estimate_cost(m)

    # optional upscale step (cheap)
    up_m = "fal-ai/clarity-upscaler"
    try:
        up = upscale_fn(url, scale=1)  # no-op scale if not needed, or keep as-is
        up_url = up.get("images", [{}])[0].get("url", url) if isinstance(up, dict) else url
    except Exception:
        up_url = url
    latency = int((time.time() - t0) * 1000)
    return WorkflowResult([up_url], up_url, round(cost, 4), latency, models_used + [up_m], {"prompt": prompt})


def product_shot(product_prompt: str, background: str = "studio", **kwargs) -> WorkflowResult:
    """flux-2-pro hero → bria remove bg."""
    t0 = time.time()
    m1 = "fal-ai/flux-2-pro"
    hero = generate(product_prompt + f" {background} background", model=m1, num_images=1, **kwargs)
    hero_url = hero["images"][0]["url"]
    m2 = "fal-ai/bria/background/remove"
    nobg = remove_bg_fn(hero_url)
    nobg_url = nobg.get("images", [{}])[0].get("url", hero_url) if isinstance(nobg, dict) else hero_url
    cost = _estimate_cost(m1) + _estimate_cost(m2)
    latency = int((time.time() - t0) * 1000)
    return WorkflowResult([nobg_url], nobg_url, round(cost, 4), latency, [m1, m2], {"background": background})


def logo_variations(brand: str, n: int = 4, **kwargs) -> WorkflowResult:
    """recraft v4 vector x n (or batch)."""
    t0 = time.time()
    m = "fal-ai/recraft/v4/text-to-vector"
    prompt = f"clean professional logo for {brand}, vector style, minimal"
    res = generate(prompt, model=m, num_images=min(n, 4), **kwargs)
    # result may contain multiple; normalize
    imgs = res.get("images", [])[:n]
    urls = [img["url"] for img in imgs] if imgs else [res.get("images", [{}])[0].get("url", "")]
    cost = _estimate_cost(m, len(urls))
    latency = int((time.time() - t0) * 1000)
    primary = urls[0] if urls else ""
    return WorkflowResult(urls, primary, round(cost, 4), latency, [m] * len(urls), {"n": len(urls), "brand": brand})


def illustration_set(prompt: str, n: int = 4, **kwargs) -> WorkflowResult:
    """krea-2 medium x n."""
    t0 = time.time()
    m = "krea/krea-2"
    res = generate(prompt, model=m, num_images=min(n, 4), **kwargs)
    imgs = res.get("images", [])[:n]
    urls = [img["url"] for img in imgs] if imgs else []
    cost = _estimate_cost(m, len(urls) or 1)
    latency = int((time.time() - t0) * 1000)
    primary = urls[0] if urls else ""
    return WorkflowResult(urls, primary, round(cost, 4), latency, [m], {"n": len(urls)})


# Additional simple ones for coverage
def hero_photoreal(prompt: str, **kwargs) -> WorkflowResult:
    m = route_use_case("hero_photoreal")
    t0 = time.time()
    res = generate(prompt, model=m, num_images=1, **kwargs)
    url = res["images"][0]["url"]
    latency = int((time.time() - t0) * 1000)
    return WorkflowResult([url], url, _estimate_cost(m), latency, [m], {"prompt": prompt})


__all__ = [
    "WorkflowResult",
    "sketch_to_hero",
    "transparent_sticker",
    "product_shot",
    "logo_variations",
    "illustration_set",
    "hero_photoreal",
]