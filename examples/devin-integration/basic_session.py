#!/usr/bin/env python3
"""basic_session.py — minimal create → wait → result.

Run:
    PYTHONPATH=skills/devin python examples/devin-integration/basic_session.py

MOCK=1 for offline.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from skills.devin.lib.devin_client import DevinClient


def main() -> None:
    client = DevinClient(dry_run=bool(os.getenv("MOCK")))
    print("Creating session...")
    sess = client.create_session(
        "Write a hello world python script and a test for it.",
        max_acu_limit=8,
    )
    sid = sess["session_id"]
    print(f"session_id={sid}")

    print("Waiting for completion (mock fast)...")
    final = client.wait_for_completion(sid, poll_interval=1, max_wait=30)
    print(f"status={final.get('status')} ACUs={final.get('acus_consumed')}")
    print("structured_output:", final.get("structured_output"))

    print("Estimated cost for 8 ACU was:", client.estimate_cost(8))


if __name__ == "__main__":
    main()