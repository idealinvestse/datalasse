# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "fal-client",
# ]
# ///

"""
Submit + poll pattern for long-running jobs.

Use when the job may take >30s (video, training, heavy workflows).
You control the polling loop and can surface logs/queue position.

Safety-off is applied via with_safety_off().

Run:
    PYTHONPATH=skills/fal-ai python skills/fal-ai/examples/submit_poll.py

Requires FAL_KEY.
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fal_client
from safety_off import with_safety_off


def main() -> None:
    if not os.getenv("FAL_KEY"):
        print("ERROR: Set FAL_KEY=...")
        sys.exit(1)

    model = "fal-ai/bytedance/seedance-2.0/text-to-video"
    args = with_safety_off(model, {
        "prompt": "a cat wearing sunglasses riding a skateboard in a cyberpunk city",
        "duration": "5",
    })

    print(f"Submitting {model} ...")
    handler = fal_client.submit(model, arguments=args)

    print(f"Request ID: {handler.request_id} (store this for webhooks or recovery)")

    while True:
        status = handler.status(with_logs=True)
        if isinstance(status, fal_client.Queued):
            print(f"  IN_QUEUE position={status.position}")
        elif isinstance(status, fal_client.InProgress):
            for log in (status.logs or []):
                print(f"  LOG: {log.get('message')}")
        elif isinstance(status, fal_client.Completed):
            print("  COMPLETED")
            break
        elif isinstance(status, fal_client.Failed):
            print("  FAILED:", status)
            sys.exit(1)
        time.sleep(0.8)

    result = handler.get()
    video = result.get("video") or result
    print("Video URL:", video.get("url") if isinstance(video, dict) else video)


if __name__ == "__main__":
    main()
