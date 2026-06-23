# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "fal-client",
# ]
# ///

"""
Subscribe pattern (default recommended pattern) with safety-off.

Workspace policy: ALL fal.ai calls go through with_safety_off() (or the
safe_client wrappers) so safety defaults are always applied.

This is the most common one-shot usage. Blocking, queue-backed, auto-retries.

Run (from repo root):
    PYTHONPATH=skills/fal-ai python skills/fal-ai/examples/subscribe_default.py

Or with uv:
    uv run --script skills/fal-ai/examples/subscribe_default.py

Requires FAL_KEY in environment.
"""

import os
import sys
from pathlib import Path

# Allow running as a standalone script without installing the skill as a package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fal_client
from safety_off import with_safety_off


def main() -> None:
    if not os.getenv("FAL_KEY"):
        print("ERROR: Set FAL_KEY=... (or FAL_API_KEY)")
        print("       export FAL_KEY=your_key")
        sys.exit(1)

    model = "fal-ai/flux-pro/v1.1-ultra"
    args = with_safety_off(model, {
        "prompt": "a serene mountain lake at sunrise, cinematic lighting, 8k",
        "aspect_ratio": "16:9",
        "raw": True,
    })

    print(f"Calling subscribe on {model} with safety-off defaults applied...")
    result = fal_client.subscribe(
        model,
        arguments=args,
        with_logs=True,
        on_queue_update=lambda update: print(f"  queue: {update}"),
    )

    if "images" in result and result["images"]:
        print("Success! First image URL:", result["images"][0]["url"])
    else:
        print("Result:", result)


if __name__ == "__main__":
    main()
