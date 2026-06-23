#!/usr/bin/env python3
"""fal-ai safety-off defaults.

Apply the most permissive user-facing safety parameters that fal.ai exposes
per-model. These are USER-CONFIGURABLE knobs — fal.ai's own platform-level
content policy operates independently and is NOT affected by these settings.

Workspace policy: ALL fal.ai calls go through `with_safety_off()` (or the
`safe_client` wrappers) so safety checker / tolerance defaults are always
set to false / "6" (most permissive).

Usage:

    from safety_off import with_safety_off, subscribe, submit, run
    import fal_client

    args = with_safety_off("fal-ai/flux-pro/v1.1-ultra", {
        "prompt": "a sunset over mountains",
        "aspect_ratio": "16:9",
        "raw": True,
    })
    result = subscribe("fal-ai/flux-pro/v1.1-ultra", args)

    # Or: direct drop-in replacement for fal_client.* functions
    result = subscribe("fal-ai/flux/dev", {"prompt": "..."})
    handler = submit("fal-ai/veo3", {"prompt": "..."})
    result = run("fal-ai/flux/schnell", {"prompt": "..."})
"""

try:
    import fal_client
    _HAS_FAL_CLIENT = True
except ImportError:
    fal_client = None  # type: ignore
    _HAS_FAL_CLIENT = False

# Per-model user-facing safety defaults.
# Models exposing enable_safety_checker (boolean): set to False.
# Models exposing safety_tolerance (enum 1-6): set to "6" (most permissive).
# Models with neither: no override applied (provider controls).
SAFETY_OFF_DEFAULTS: dict[str, dict] = {
    # --- enable_safety_checker ---
    "fal-ai/flux/schnell":                {"enable_safety_checker": False},
    "fal-ai/flux/dev":                    {"enable_safety_checker": False},
    "fal-ai/flux-2-pro":                  {"enable_safety_checker": False, "safety_tolerance": "6"},
    "fal-ai/flux-kontext-lora":           {"enable_safety_checker": False},
    "ideogram/v4":                        {"enable_safety_checker": False},
    "alibaba/happy-horse/text-to-video":  {"enable_safety_checker": False},
    # --- safety_tolerance ---
    "fal-ai/flux-pro/v1.1-ultra":         {"safety_tolerance": "6"},
    "fal-ai/flux-pro/kontext":            {"safety_tolerance": "6"},
    "fal-ai/nano-banana-2":               {"safety_tolerance": "6"},
    "fal-ai/nano-banana-2/edit":          {"safety_tolerance": "6"},
    "fal-ai/veo3":                        {"safety_tolerance": "6"},
}


def with_safety_off(model_id: str, args: dict | None = None) -> dict:
    """Merge user `args` with workspace safety-off defaults for `model_id`.

    User-provided values WIN over defaults (explicit override allowed).
    Models not in SAFETY_OFF_DEFAULTS pass through unchanged.
    """
    defaults = SAFETY_OFF_DEFAULTS.get(model_id, {})
    merged = dict(defaults)
    if args:
        merged.update(args)  # user args override defaults
    return merged


def subscribe(model_id: str, arguments: dict | None = None, **kwargs):
    """Drop-in replacement for fal_client.subscribe with safety-off defaults."""
    if not _HAS_FAL_CLIENT:
        raise RuntimeError("fal_client not installed; pip install fal-client")
    return fal_client.subscribe(model_id, arguments=with_safety_off(model_id, arguments), **kwargs)


def submit(model_id: str, arguments: dict | None = None, **kwargs):
    """Drop-in replacement for fal_client.submit with safety-off defaults."""
    if not _HAS_FAL_CLIENT:
        raise RuntimeError("fal_client not installed; pip install fal-client")
    return fal_client.submit(model_id, arguments=with_safety_off(model_id, arguments), **kwargs)


def run(model_id: str, arguments: dict | None = None, **kwargs):
    """Drop-in replacement for fal_client.run with safety-off defaults."""
    if not _HAS_FAL_CLIENT:
        raise RuntimeError("fal_client not installed; pip install fal-client")
    return fal_client.run(model_id, arguments=with_safety_off(model_id, arguments), **kwargs)


# Public models that have NO user-facing safety toggle (provider-only):
NO_USER_SAFETY_MODELS = {
    "krea/v2/medium/text-to-image",
    "openai/gpt-image-2/edit",
    "bytedance/seedance-2.0/text-to-video",
    "bytedance/seedance-2.0/fast/text-to-video",
    "bria/fibo-edit/edit",
    "bytedance/seedance-2.0/fast/image-to-video",
    "bytedance/seedance-2.0/fast/reference-to-video",
    "luma/agent/ray/v3.2/image-to-video",
    "fal-ai/kling-video/v3/pro/image-to-video",
    "fal-ai/stable-audio-25/text-to-audio",
    "fal-ai/minimax-music/v2.6",
    "fal-ai/ace-step",
    "fal-ai/elevenlabs/tts/turbo-v2.5",
    "fal-ai/elevenlabs/tts/multilingual-v2",
    "fal-ai/whisper",
    "fal-ai/florence-2-large/detailed-caption",
    "fal-ai/trellis",
    "tripo3d/p1/image-to-3d",
}


if __name__ == "__main__":
    # Quick self-test
    import sys
    if len(sys.argv) < 2:
        print("Usage: safety_off.py <model_id> [key=value ...]")
        print()
        print("Configured models with safety-off defaults:")
        for m in sorted(SAFETY_OFF_DEFAULTS):
            print(f"  {m}: {SAFETY_OFF_DEFAULTS[m]}")
        sys.exit(0)

    model = sys.argv[1]
    args = {}
    for kv in sys.argv[2:]:
        k, _, v = kv.partition("=")
        args[k] = v
    print(with_safety_off(model, args))