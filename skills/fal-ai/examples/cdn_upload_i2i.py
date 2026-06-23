# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "fal-client",
# ]
# ///

"""
CDN upload + image-to-image example.

Upload a local file (or use URL), then pass the fal CDN url to an edit model.
Uses safety-off.

Run:
    PYTHONPATH=skills/fal-ai python skills/fal-ai/examples/cdn_upload_i2i.py /path/to/ref.jpg

If no local file arg, demonstrates with a public URL (still uploads via fal for consistency).

Requires FAL_KEY.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fal_client
from safety_off import with_safety_off


def main() -> None:
    if not os.getenv("FAL_KEY"):
        print("ERROR: Set FAL_KEY=...")
        sys.exit(1)

    local_ref = sys.argv[1] if len(sys.argv) > 1 else None

    if local_ref and Path(local_ref).exists():
        print(f"Uploading local file: {local_ref}")
        ref_url = fal_client.upload_file(local_ref)
    else:
        print("No local file or file not found. Using public URL example (upload recommended for private files).")
        # A public demo image; in real use always prefer upload_file for controlled assets
        ref_url = "https://fal.media/files/kangaroo/demo-reference.jpg"
        # To be strict, we can still "upload" it if desired, but for demo just use as-is.
        # ref_url = fal_client.upload_image(...)  # if you have bytes/PIL

    print(f"Reference CDN URL: {ref_url}")

    model = "fal-ai/flux-pro/v1.1-ultra"
    args = with_safety_off(model, {
        "prompt": "turn the scene into a vibrant sunset, golden hour, dramatic clouds",
        "image_url": ref_url,
        "image_prompt_strength": 0.55,
        "aspect_ratio": "16:9",
    })

    result = fal_client.subscribe(model, arguments=args)
    out_url = result["images"][0]["url"] if result.get("images") else result
    print("Edited image URL:", out_url)


if __name__ == "__main__":
    main()
