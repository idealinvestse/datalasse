# fal-image (Q3 2026 — Production Optimized)

**Status:** Complete registry (24+ models), use-case routing (11 chains), workflows, CLI, tests. Ready for production.

Orchestrates **all** fal.ai image generation intelligently using the Q3 2026 landscape. Primary recommendation: `fal-ai/flux-2-pro` as new default all-rounder.

The broader `fal-ai` skill handles video, audio, 3D, LLM-proxy, advanced workflows.

## When to use this skill

- Generate/edit images with intelligent per-use-case model selection.
- Need automatic workspace safety-off (`enable_safety_checker=false` + `safety_tolerance=6`).
- Want capability-aware registry, use-case routing, multi-step workflows, or vector/transparent/upscale.
- CLI or Python API for batch, variations, cost estimation.

## When NOT to use this skill

- Non-image fal tasks (use `fal-ai` skill).
- Simple one-off that OpenClaw `image_generate` already covers perfectly (you can still pass `model="fal/..."`).

## Quick Start

```python
from skills.fal_image import generate, generate_for_use_case, list_models

# Default (now flux-2-pro)
result = generate("studio portrait of a fox, photoreal, soft lighting")
print(result["images"][0]["url"])

# Use-case routing (auto or explicit)
result = generate_for_use_case("logo_text_poster", "minimal logo for Moss AI, sans-serif, clean")

# List capabilities
print(len(list_models()))  # >= 24
```

CLI:
```bash
bin/fal-image generate "red apple on marble" --use-case hero_photoreal --aspect 16:9
bin/fal-image route hero_photoreal
bin/fal-image doctor
bin/fal-image list --tier premium
```

## Model Registry (24+ models)

| Model ID                                   | Tier     | Cost   | Key Use Cases                  | Notes |
|--------------------------------------------|----------|--------|--------------------------------|-------|
| fal-ai/flux-2-pro (PRIMARY)                | premium  | $0.03  | hero_photoreal, social         | New top all-rounder. 9 refs, JSON/HEX. |
| fal-ai/flux/schnell                        | fast     | $0.003 | sketch_draft_quick             | Cheapest/fastest draft. |
| fal-ai/flux/dev                            | balanced | $0.025 | sketch, general                | Balanced, LoRA capable. |
| fal-ai/flux-pro/v1.1-ultra                 | premium  | $0.06  | hero_photoreal                 | High-res fallback. |
| ideogram/v4                                | balanced | $0.03+ | logo_text_poster, transparent  | Text/logo/alpha king. |
| fal-ai/recraft/v4/text-to-image            | balanced | $0.04  | logo, illustration             | Design-grade. |
| fal-ai/recraft/v4/text-to-vector           | balanced | $0.08  | vector_svg_icon                | Native SVG. |
| fal-ai/recraft/v4/pro/*                    | premium  | $0.25+ | premium brand                  | Pro raster/vector. |
| fal-ai/gpt-image-2                         | premium  | $0.04+ | complex_text_heavy, logo       | Perfect text adherence. |
| fal-ai/nano-banana-2 (+/edit)              | balanced | $0.08  | social_vertical, edit          | 14 refs, character consistency. |
| krea/krea-2                                | balanced | $0.03  | illustration_anime             | Artistic, anime, painting. |
| fal-ai/bytedance/seedream/v4.5 + v5/lite   | balanced/fast | $0.035-0.04 | hero, sketch | Web-grounded, reasoning. |
| fal-ai/qwen-image-2 (+pro)                 | balanced/premium | $0.035-0.075 | illustration, text-heavy | Typography/infographics. |
| fal-ai/flux-2-pro/edit + kontext*          | premium  | $0.03-0.06 | edit_modify                    | Strong editing. |
| fal-ai/clarity-upscaler / esrgan           | balanced/fast | $0.01 / 0.005 | upscale | High-fidelity upscale. |
| fal-ai/bria/background/remove + rembg      | balanced/fast | $0.018 / 0.001 | background_removal, sticker | Alpha removal. |

Full authoritative list + metadata in `registry.py`. Prices/latency from research (2026-07-01).

## Use-Case Routing (11 chains)

Auto-detect + explicit:

```python
from skills.fal_image import generate_for_use_case, route_use_case, detect_use_case

uc = detect_use_case("9:16 vertical story for instagram")
model = route_use_case(uc)  # nano-banana-2 or flux-2-pro
res = generate_for_use_case(uc, prompt)
```

Chains (verbatim research):
- `hero_photoreal`: flux-2-pro → flux-pro/v1.1-ultra → seedream v4.5
- `logo_text_poster`: ideogram/v4 → gpt-image-2 → recraft/v4
- `vector_svg_icon`: recraft/v4/vector → ideogram → recraft/v3
- `transparent_sticker`: ideogram/v4 → flux-2-pro → recraft vector
- `sketch_draft_quick`: flux/schnell → flux/dev → seedream v5/lite
- `social_vertical`: nano-banana-2 → flux-2-pro → seedream
- `illustration_anime`: krea/krea-2 → recraft/v4 → qwen-2
- `edit_modify`: flux-2-pro/edit → nano-banana-2/edit → gpt-image-2/i2i
- `upscale`: clarity-upscaler → esrgan
- `background_removal`: bria/remove → imageutils/rembg
- `complex_text_heavy`: gpt-image-2 → nano-banana-pro → qwen-pro

## Workflows (multi-step)

```python
from skills.fal_image.workflows import (
    sketch_to_hero, transparent_sticker, product_shot,
    logo_variations, illustration_set, WorkflowResult
)

wr: WorkflowResult = sketch_to_hero("quick house concept")
print(wr.primary_url, wr.total_cost_usd, wr.models_used)
```

Workflows:
- `sketch_to_hero`: schnell → flux-2-pro → clarity
- `transparent_sticker`: ideogram/v4 (+upscale)
- `product_shot`: flux-2-pro → bria remove
- `logo_variations(brand, n=4)`: recraft vector
- `illustration_set(prompt, n=4)`: krea-2
- `hero_photoreal` helper

All return `WorkflowResult(output_urls, primary_url, total_cost_usd, total_latency_ms, models_used, metadata)`.

## CLI Reference

```bash
bin/fal-image generate <prompt> [--use-case X] [--model Y] [--aspect 16:9] [--output path]
bin/fal-image edit <image> <prompt> [--model Y] [--strength 0.7]
bin/fal-image upscale <image> [--scale 2] [--model clarity|esrgan]
bin/fal-image remove-bg <image>
bin/fal-image vector <prompt> [--output path.svg]
bin/fal-image variations <image> [--n 4]
bin/fal-image list [--feature edit] [--tier premium] [--family flux]
bin/fal-image route <use-case>          # shows full chain
bin/fal-image doctor                    # FAL_KEY + registry health
bin/fal-image cost <prompt> [--use-case]
```

All support `--dry-run --json`.

## API Reference (key signatures)

- `generate(prompt, model=None, aspect_ratio="16:9", num_images=1, **kwargs)`
- `generate_for_use_case(use_case, prompt, **kwargs)`
- `edit(image_url, prompt, model=None, strength=0.7, ...)`
- `upscale(image_url, scale=2, model=None)`
- `remove_background(image_url, model=None)`
- `make_vector(prompt, model=None)`
- `make_transparent(...)`
- `batch_generate(prompts, ...)`
- `list_models(feature=None, tier=None, family=None, use_case=None)`
- `route_use_case(use_case, prefer_speed=False) -> str`
- `detect_use_case(prompt) -> str`
- `WorkflowResult(...)`

See `client.py`, `router.py`, `workflows.py`, `registry.py`.

## Integration with OpenClaw `image_generate`

```python
image_generate(
    prompt="...",
    model="fal/fal-ai/flux-2-pro",   # new primary
    aspect_ratio="16:9",
    # safety_tolerance handled by provider + our wrappers
)
```

The `fal_image` module gives you smarter routing and advanced ops beyond the basic provider.

## Safety Policy (Enforced)

Every call goes through `with_safety_off` (source: `skills/fal-ai/safety_off.py`):
- `enable_safety_checker=false`
- `safety_tolerance="6"` (max permissive)

User args override. Platform policy still applies (CSAM etc.).

See `bin/fal-safety-audit`.

## Test Guide

```bash
# Unit tests (no FAL_KEY needed)
MOCK=1 pytest skills/fal_image/tests/ -v --tb=short

# With coverage
MOCK=1 pytest skills/fal_image/tests/ --cov=skills.fal_image --cov-report=term-missing

# Smoke (requires FAL_KEY)
bin/fal-image generate "red apple" --use-case hero_photoreal --output /tmp/test.png
```

Target: ≥80% coverage. Mocks cover all paths.

## Cost Optimization Tips (from research)

- Start with `sketch_draft_quick` / schnell for iteration ($0.003).
- Promote only winners to flux-2-pro / premium.
- Use `num_images` batching where supported.
- Prefer vector (recraft) for logos/icons (scalable, no extra upscale).
- Native transparent (ideogram) avoids extra bg-remove cost.
- Cache identical (prompt+model+seed) client-side 1h.
- Max budget guidance: $0.15/image total across fallbacks.

## Migration Notes

- **Primary changed** from `fal-ai/flux/dev` → `fal-ai/flux-2-pro`.
- Old models remain in registry for fallbacks/compat.
- If `fal-ai/flux-2-pro` endpoint unavailable at runtime, code falls back gracefully (warn + dev).
- Update any hard-coded "flux/dev" strings if you want the new default.
- `openclaw.json` updated (backup taken before change).

## File Structure

```
skills/fal_image/
├── SKILL.md
├── __init__.py
├── registry.py          # 24+ ModelInfo + list/choose
├── router.py            # 11 chains + detect/route
├── client.py            # generate/edit + new high-level
├── workflows.py         # WorkflowResult + 5 workflows
├── safety.py            # thin re-export
├── utils.py             # upload + improved estimate_cost
├── examples/
└── tests/
    ├── conftest.py
    ├── test_registry.py
    ├── test_router.py
    ├── test_safety.py
    ├── test_client.py
    └── test_workflows.py
```

bin/fal-image (executable)

## Development Notes

- Registry = single source of truth. Update when fal adds models.
- All generation paths enforce safety via fal-ai/safety_off.
- Keep public API stable.
- Run tests with MOCK=1 before any commit touching this skill.

Research date: 2026-07-01 (deepseek-v4-pro). 50 sources.

For advanced (webhooks, realtime, video, custom serverless) use `skills/fal-ai/`.