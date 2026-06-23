# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "fal-client",
# ]
# ///

"""
Submit + webhook pattern (production async for long jobs).

Fire-and-forget with webhook callback. Ideal for video, training, heavy workflows.
Store the request_id. Handler must be idempotent.

Safety-off applied automatically.

Run:
    PYTHONPATH=skills/fal-ai python skills/fal-ai/examples/submit_webhook.py

Requires FAL_KEY. You must provide a real webhook_url that can receive POSTs.
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

    model = "fal-ai/bytedance/seedance-2.0/text-to-video"
    webhook_url = os.getenv("FAL_WEBHOOK_URL", "https://example.com/api/fal/webhook")

    args = with_safety_off(model, {"prompt": "sunset timelapse over ocean"})

    print(f"Submitting {model} with webhook...")
    handler = fal_client.submit(
        model,
        arguments=args,
        webhook_url=webhook_url,
    )

    print(f"handler.request_id = {handler.request_id}")
    print("Send this ID + expect POST to your webhook_url.")
    print("Webhook payload will contain status, payload or error.")


if __name__ == "__main__":
    main()
