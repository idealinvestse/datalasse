#!/usr/bin/env python3
"""telegram_notifier.py — long session with completion notification.

Illustrates polling loop + sending message via existing openclaw tooling.

In real usage the 'message' would be:
  openclaw message send --channel telegram --target 438805461 --message "..."

Run:
    PYTHONPATH=skills/devin MOCK=1 python examples/devin-integration/telegram_notifier.py
"""

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from skills.devin.lib.devin_client import DevinClient


def notify(text: str) -> None:
    """Send via openclaw if available, else print."""
    try:
        subprocess.run(
            [
                "openclaw", "message", "send",
                "--channel", "telegram",
                "--target", "438805461",
                "--message", text,
            ],
            check=False, timeout=15
        )
    except Exception:
        print("[NOTIFY would send]", text)


def main() -> None:
    client = DevinClient(dry_run=bool(os.getenv("MOCK")))
    sid = client.create_session(
        "Refactor the legacy parser and ensure backward compat. This may take a while.",
        max_acu_limit=40,
        tags=["migration", "long"],
    )["session_id"]
    print("long session started:", sid)

    def progress(st: str, s: dict) -> None:
        if st == "running":
            print("still running... acu so far", s.get("acus_consumed"))

    final = client.wait_for_completion(sid, poll_interval=8, max_wait=3600, on_status=progress)

    result = final.get("structured_output") or final.get("result") or str(final)
    notify(f"Devin session {sid} finished: {final.get('status')}\nACU: {final.get('acus_consumed')}\nResult: {result}")


if __name__ == "__main__":
    main()