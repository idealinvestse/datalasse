"""fal-image safety layer.

Thin re-export + image-specific extensions of the workspace safety-off policy.
Source of truth remains `skills/fal-ai/safety_off.py`.

All image generation in this workspace MUST go through `with_safety_off`
(or the thin wrappers here) so the permissive safety defaults are consistently
applied.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Import the canonical implementation from fal-ai skill
# New Q3 models (flux-2-pro/edit etc) are covered via fal-ai/safety_off.py updates.
_fal_ai_safety = Path(__file__).parent.parent / "fal-ai" / "safety_off.py"

if _fal_ai_safety.exists():
    # Dynamic import to avoid circular issues
    import importlib.util
    spec = importlib.util.spec_from_file_location("fal_ai_safety_off", _fal_ai_safety)
    fal_ai_safety = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fal_ai_safety)

    with_safety_off = fal_ai_safety.with_safety_off
    subscribe = fal_ai_safety.subscribe
    submit = fal_ai_safety.submit
    run = fal_ai_safety.run
    SAFETY_OFF_DEFAULTS = fal_ai_safety.SAFETY_OFF_DEFAULTS
    NO_USER_SAFETY_MODELS = fal_ai_safety.NO_USER_SAFETY_MODELS
else:
    # Fallback: minimal inline copy (should never happen in normal operation)
    SAFETY_OFF_DEFAULTS = {}
    NO_USER_SAFETY_MODELS = set()

    def with_safety_off(model_id: str, args: dict | None = None) -> dict:
        return dict(args) if args else {}


__all__ = [
    "with_safety_off",
    "subscribe",
    "submit",
    "run",
    "SAFETY_OFF_DEFAULTS",
    "NO_USER_SAFETY_MODELS",
]

if __name__ == "__main__":
    # Allow direct testing: python skills/fal-image/safety.py flux-pro/v1.1-ultra
    model = sys.argv[1] if len(sys.argv) > 1 else "fal-ai/flux-pro/v1.1-ultra"
    print(with_safety_off(model, {"prompt": "test"}))