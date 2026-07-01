#!/usr/bin/env python3
"""batch_migration.py — run N scoped sessions in parallel safely.

Uses asyncio + semaphore to avoid quota storms.
Cost: N * max_acu_limit.

MOCK=1 safe.
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from skills.devin.lib.devin_client import DevinClient


async def run_one(client: DevinClient, prompt: str, max_acu: int, sem: asyncio.Semaphore) -> dict:
    async with sem:
        sess = client.create_session(prompt, max_acu_limit=max_acu)
        sid = sess["session_id"]
        print(f"started {sid}")
        # In real: await would be thread executor or polling thread
        # For demo we use sync wait inside (acceptable for example)
        final = client.wait_for_completion(sid, poll_interval=1, max_wait=30)
        print(f"done {sid} acu={final.get('acus_consumed')}")
        return final


async def main() -> None:
    client = DevinClient(dry_run=bool(os.getenv("MOCK")))
    tasks = [
        "Migrate utils.py to use pathlib",
        "Add type hints to auth module",
        "Generate tests for payment flow",
    ]
    sem = asyncio.Semaphore(2)  # limit concurrency
    coros = [run_one(client, t, 12, sem) for t in tasks]
    results = await asyncio.gather(*coros)
    print(f"batch complete: {len(results)} sessions")


if __name__ == "__main__":
    asyncio.run(main())