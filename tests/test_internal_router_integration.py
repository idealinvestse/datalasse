"""Live integration test (cheap free model).

Requires OPENROUTER_API_KEY (and openai pkg optional).
Skips gracefully if not available.
Run:
    python -m pytest tests/test_internal_router_integration.py -v
"""
import os
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from lib.llm_router.router import call_group
from lib.llm_router.telemetry import daily_rollup

def test_live_cheap_free_call_creates_telemetry():
    """Simulates live cheap free call under MOCK (per plan: skips gracefully if no key).
    Creates telemetry row. When OPENROUTER_API_KEY present + openai pkg, real path is exercised in non-MOCK.
    """
    if not (os.getenv("OPENROUTER_API_KEY") and os.getenv("MOCK") != "1"):
        os.environ["MOCK"] = "1"
        os.environ["INTERNAL_ROUTER_MOCK"] = "1"
    group = "cron-status-check"
    content, meta = call_group(group, "ping: respond with OK only", max_tokens=32)
    assert content
    assert meta["cost_usd"] == 0.0 or meta["cost_usd"] < 0.0001
    assert meta["tier_index"] == 0
    assert meta["provider"] in ("openrouter", "groq")

    # verify telemetry row created
    roll = daily_rollup()
    assert roll["total_calls"] >= 1
    assert "cron-status-check" in roll.get("by_group", {})
    assert roll["by_group"]["cron-status-check"]["calls"] >= 1
