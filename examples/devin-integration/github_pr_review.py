#!/usr/bin/env python3
"""github_pr_review.py — PR review with structured output schema.

Prompt includes PR URL. Uses schema for consistent review output.

Run with MOCK=1.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from skills.devin.lib.devin_client import DevinClient


SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "risks": {"type": "array", "items": {"type": "string"}},
        "suggestions": {"type": "array", "items": {"type": "string"}},
        "approve": {"type": "boolean"},
    },
    "required": ["summary", "risks", "suggestions", "approve"],
}


def main() -> None:
    client = DevinClient(dry_run=bool(os.getenv("MOCK")))
    pr_url = "https://github.com/example/repo/pull/42"
    prompt = f"Review the changes in {pr_url}. Be thorough but concise."

    sess = client.create_session(
        prompt,
        max_acu_limit=25,
        structured_output_schema=SCHEMA,
        tags=["pr-review"],
    )
    sid = sess["session_id"]
    print("created", sid)

    final = client.wait_for_completion(sid, poll_interval=2, max_wait=60)
    print("review result:")
    print(final.get("structured_output"))


if __name__ == "__main__":
    main()