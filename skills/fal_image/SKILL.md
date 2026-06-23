# fal-image (updated 2026-06-22)

**Status:** MVP complete — ready for production use.

Orchestrates all fal.ai image generation with a central model registry, mandatory safety-off enforcement, smart defaults, editing workflows, and high-level helpers.

This skill owns **everything image-related** via fal.ai. The broader `fal-ai` skill handles video, audio, workflows, 3D, and LLM-proxy usage.

**Note:** A duplicate "create" skill_workshop proposal was incorrectly filed on 2026-06-22 (the directory and implementation already existed). The skill is fully operational.

## When to use this skill

- You want to generate or edit images using any fal.ai image model.
- You want automatic enforcement of the workspace safety-off policy (`enable_safety_checker=false` + `safety_tolerance=6`).
- You want a capability-aware model registry instead of hardcoding model IDs everywhere.
- You need edit workflows, multi-reference support, batch/variations, or intelligent model routing.

## When NOT to use this skill

- Non-image fal.ai tasks (use `fal-ai` skill directly).
- Simple one-off calls that OpenClaw's built-in `image_generate` already covers (you can still override the model via `model="fal/fal-ai/..."`).

## Quick Start

```python
from skills.fal_image import generate, edit

# Simple generation (safety-off enforced automatically)
result = generate("a cyberpunk cat wearing neon sunglasses, cinematic lighting")
print(result["images"][0]["url"])

# Editing with reference image
result = edit(
    image_url="https://fal.media/files/.../cat.png",
    prompt="make it sunset over mountains, dramatic golden hour",
    strength=0.65
)
```

## Core API

### `generate(prompt, model=None, **kwargs)`
High-level generation entrypoint. Picks a sensible default model if none provided, applies safety-off, and returns the result.

### `edit(image_url, prompt, model=None, strength=0.7, **kwargs)`
Unified image-to-image / editing interface. Automatically handles reference image upload when a local path is passed.

### `batch_generate(prompts, model=None, **kwargs)`
Generate multiple prompts in parallel (uses `submit` + polling internally).

### `variations(image_url, n=4, model=None, **kwargs)`
Create N variations of a reference image.

### Registry helpers
- `get_model(model_id)` — full metadata for a model
- `list_models(feature="edit")` — filter by capability
- `choose_model(requirements)` — smart router (cost, quality, speed, max_refs, etc.)

## Safety Policy (Enforced)
Every call automatically merges:
- `enable_safety_checker=false` (when supported)
- `safety_tolerance=6` (maximum permissiveness)

User-provided args **override** defaults when explicitly set.

## Supported Models (MVP)

| Model ID                        | Type     | Max Refs | Edit | Notes                          |
|---------------------------------|----------|----------|------|--------------------------------|
| `fal-ai/flux/schnell`           | t2i      | 0        | No   | Fastest, cheapest              |
| `fal-ai/flux/dev`               | t2i/i2i  | 1        | Yes  | Balanced quality               |
| `fal-ai/flux-pro/v1.1-ultra`    | t2i/i2i  | 1        | Yes  | Highest quality, premium       |
| `fal-ai/nano-banana-2`          | edit     | 14       | Yes  | Excellent multi-ref editor     |
| `fal-ai/ideogram/v4`            | t2i      | 0        | No   | Strong typography              |
| `fal/krea/v2/large/text-to-image` | t2i    | 10       | No   | High creativity                |

See `registry.py` for the full authoritative list and capability matrix.

## File Structure
```
skills/fal_image/
├── SKILL.md
├── __init__.py          # Public API exports
├── registry.py          # MODEL_REGISTRY + capability lookup
├── client.py            # generate(), edit(), wrappers
├── safety.py            # Safety-off merging (extends fal-ai/safety_off)
├── utils.py             # upload, aspect helpers, cost stubs
├── examples/
│   ├── basic_generate.py
│   ├── edit_workflow.py
│   └── smart_router.py
└── tests/
```

## Integration with OpenClaw
You can call via the built-in provider:
```python
image_generate(
    prompt="...",
    model="fal/fal-ai/flux-pro/v1.1-ultra",
    safety_tolerance="6"   # still respected
)
```

Or use the orchestrator directly for more control:
```python
from skills.fal_image import generate
result = generate(prompt="...", model="fal-ai/flux-pro/v1.1-ultra")
```

## Development Notes
- Always import safety logic from `./safety.py` (never duplicate the mapping).
- Registry is the single source of truth — update it when adding models.
- Keep the public API surface small and stable.

---
*Created 2026-06-19 via skill workshop proposal. MVP implementation in progress.*