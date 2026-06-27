"""Telemetry: append jsonl + rollup + hourly state for caps.

Files under memory/research/ (or policy telemetry_dir).
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def _get_telemetry_dir(cfg: dict[str, Any] | None = None) -> Path:
    base = "memory/research"
    if cfg and "policy" in cfg:
        base = cfg["policy"].get("telemetry_dir", base)
    p = Path(base)
    p.mkdir(parents=True, exist_ok=True)
    return p

def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def append_telemetry(
    record: dict[str, Any],
    cfg: dict[str, Any] | None = None,
) -> Path:
    """Append one row to llm-router-telemetry-YYYY-MM-DD.jsonl . Returns path."""
    d = _get_telemetry_dir(cfg)
    fname = f"llm-router-telemetry-{_today()}.jsonl"
    path = d / fname
    rec = dict(record)
    rec.setdefault("ts", datetime.now(timezone.utc).isoformat())
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return path

def daily_rollup(date: str | None = None, cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return summary for the day."""
    d = _get_telemetry_dir(cfg)
    if not date:
        date = _today()
    path = d / f"llm-router-telemetry-{date}.jsonl"
    summary: dict[str, Any] = {
        "date": date,
        "total_calls": 0,
        "total_cost_usd": 0.0,
        "by_group": {},
        "escalations": 0,
        "errors": {},
    }
    if not path.exists():
        return summary
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            g = r.get("task_group", "unknown")
            c = r.get("cost_usd", 0.0) or 0.0
            summary["total_calls"] += 1
            summary["total_cost_usd"] += c
            bg = summary["by_group"].setdefault(g, {"calls": 0, "cost": 0.0, "escalations": 0})
            bg["calls"] += 1
            bg["cost"] += c
            ti = r.get("tier_index", 0) or 0
            if ti > 0:
                bg["escalations"] += 1
                summary["escalations"] += 1
            err = r.get("error_class")
            if err:
                summary["errors"][err] = summary["errors"].get(err, 0) + 1
    summary["total_cost_usd"] = round(summary["total_cost_usd"], 8)
    for bg in summary["by_group"].values():
        bg["cost"] = round(bg["cost"], 8)
    return summary

# Simple hourly cap state (memory/llm-router-state.json)
STATE_PATH = Path("memory/llm-router-state.json")

def load_hourly_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"hour": "", "groups": {}}
    try:
        with STATE_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"hour": "", "groups": {}}

def save_hourly_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    tmp.replace(STATE_PATH)

def update_and_check_cap(group: str, cost: float, per_hour_cap: float) -> tuple[bool, float]:
    """Add cost (if >0), check against hour cap. Return (allowed, spent_after). Resets on hour change.
    Pre-call should pass cost=0.0 to avoid mutating counts.
    """
    now = datetime.now(timezone.utc)
    hour_key = now.strftime("%Y-%m-%dT%H")
    state = load_hourly_state()
    if state.get("hour") != hour_key:
        state = {"hour": hour_key, "groups": {}}
    gstate = state["groups"].setdefault(group, {"spent_usd": 0.0, "calls": 0})
    new_spent = round(gstate["spent_usd"] + cost, 8)
    gstate["spent_usd"] = new_spent
    if cost > 0:
        gstate["calls"] += 1
    save_hourly_state(state)
    allowed = new_spent <= (per_hour_cap + 1e-9)
    return allowed, new_spent
