# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "fal-client",
# ]
# ///

"""
Stream a workflow (chained models) with intermediate events.

Workflows use `stream()` (not subscribe) so you get submit/completion/output/error per node.

Safety-off applied via with_safety_off().

Run:
    PYTHONPATH=skills/fal-ai python skills/fal-ai/examples/workflow_stream.py

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

    # Example workflow id (adjust to a real published one in your account or public)
    workflow = "workflows/fal-ai/sdxl-sticker"
    args = with_safety_off(workflow, {
        "prompt": "a cute robotic puppy, pixar style, vibrant colors",
    })

    print(f"Streaming workflow {workflow} ...")
    try:
        stream = fal_client.stream(workflow, arguments=args)
        for event in stream:
            print(event)
            if event.get("type") == "output":
                print("Final output received.")
    except Exception as e:
        print(f"Stream error (common if workflow id is example-only): {e}")
        print("This script shows the correct streaming + safety-off pattern.")


if __name__ == "__main__":
    main()
