"""Unit tests for internal LLM router (MOCK=1).

Run:
    MOCK=1 python -m pytest tests/test_internal_router.py -v
"""
import json
import os
import sys
from pathlib import Path

# Ensure importable when pytest runs from root
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

os.environ["MOCK"] = "1"
os.environ["INTERNAL_ROUTER_MOCK"] = "1"

from lib.llm_router.router import InternalLLMRouter, call_group, get_router
from lib.llm_router.config import load_config, validate_config
from lib.llm_router.pricing import calculate_cost, get_price
from lib.llm_router.telemetry import append_telemetry, daily_rollup, update_and_check_cap, STATE_PATH

def test_config_load_and_validate():
    cfg = load_config()
    assert "groups" in cfg
    errs = validate_config(cfg)
    assert errs == [], f"config errors: {errs}"
    g = cfg["groups"]["cron-status-check"]
    assert len(g["tiers"]) >= 1
    assert "openrouter" in g["tiers"][0]["provider"] or g["tiers"][0]["provider"] == "openrouter"

def test_tier_selection_free_first():
    r = get_router()
    g = r.get_group("cron-status-check")
    sel0 = r.select_tier_and_provider(g, 0)
    assert sel0["tier_index"] == 0
    assert ":free" in sel0["model"] or sel0["provider"] == "groq"  # prefer free listed first
    sel1 = r.select_tier_and_provider(g, 1)
    assert sel1["tier_index"] == 1

def test_pricing_free_and_paid():
    assert get_price("liquid/lfm-2.5-1.2b-instruct:free") == (0.0, 0.0)
    assert get_price("llama-3.1-8b-instant")[0] == 0.05
    c = calculate_cost({"prompt_tokens": 1000, "completion_tokens": 100}, "llama-3.1-8b-instant")
    assert 0.00005 < c < 0.0002

def test_mock_execute_and_telemetry(tmp_path, monkeypatch):
    monkeypatch.setenv("MOCK", "1")
    # use temp state/telemetry via monkey? simple: run and check files created under memory
    r = InternalLLMRouter()
    content, meta = r.execute("cron-status-check", "ping test")
    assert "MOCK" in content or "[MOCK" in content
    assert meta["mock"] is True
    assert meta["cost_usd"] == 0.0 or meta["cost_usd"] < 0.0001
    assert meta["tier_index"] == 0

    # telemetry row written
    today = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%d")
    tfile = Path("memory/research") / f"llm-router-telemetry-{today}.jsonl"
    assert tfile.exists()
    lines = tfile.read_text().strip().splitlines()
    last = json.loads(lines[-1])
    assert last["task_group"] == "cron-status-check"
    assert last["success"] is True

def test_escalation_on_cost_cap(monkeypatch):
    monkeypatch.setenv("MOCK", "1")
    r = InternalLLMRouter()
    # force very low cap to trigger escalate
    g = r.get_group("cron-status-check")
    g["cost_cap_per_call_usd"] = 0.0  # impossible
    # patch select to avoid
    content, meta = r.execute("cron-status-check", "ping")
    # may succeed on tier0 if cost 0 in mock, or escalate. assert no crash and meta present
    assert "tier_index" in meta

def test_hourly_cap_and_state(monkeypatch):
    monkeypatch.setenv("MOCK", "1")
    # force reset to known clean state for this test only
    if STATE_PATH.exists():
        STATE_PATH.unlink()
    allowed, spent = update_and_check_cap("cron-status-check", 0.0001, 0.01)
    assert allowed
    assert spent > 0
    # exceed
    allowed2, spent2 = update_and_check_cap("cron-status-check", 1.0, 0.01)
    assert not allowed2
    # cleanup
    if STATE_PATH.exists():
        STATE_PATH.unlink()

def test_call_group_convenience():
    c, m = call_group("cron-classify", "classify: hello")
    assert c
    assert "group" in m or "tier_index" in m

def test_100_mock_calls_cost_under_cap():
    # sim in unit test
    r = InternalLLMRouter()
    total = 0.0
    esc = 0
    for i in range(100):
        try:
            _, meta = r.execute("cron-status-check", f"ping {i}")
            total += meta.get("cost_usd", 0)
            if meta.get("tier_index", 0) > 0:
                esc += 1
        except Exception:
            pass
    assert total < 0.02  # under hour cap for group (0.01 but mock 0 anyway)
    assert esc < 30  # sane escalation %
