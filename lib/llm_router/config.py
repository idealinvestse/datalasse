"""Config loader for internal LLM router.

Loads from lib/llm_router/config.example.json (relative to this file) or accepts dict.
Validation minimal for Phase 1.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.example.json"

def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load config. Falls back to embedded defaults if file missing."""
    if path is None:
        p = DEFAULT_CONFIG_PATH
    else:
        p = Path(path)
    if p.exists():
        with p.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        # Minimal embedded defaults matching plan (subset for safety)
        cfg = {
            "version": "1.0",
            "providers": {
                "openrouter": {"base_url": "https://openrouter.ai/api/v1", "api_key_env": "OPENROUTER_API_KEY"},
                "groq": {"base_url": "https://api.groq.com/openai/v1", "api_key_env": "GROQ_API_KEY"},
            },
            "groups": {
                "cron-status-check": {
                    "description": "Heartbeat etc (free-first)",
                    "cost_cap_per_call_usd": 0.0005,
                    "cost_cap_per_hour_usd": 0.01,
                    "default_max_tokens": 128,
                    "tiers": [
                        {"provider": "openrouter", "model": "liquid/lfm-2.5-1.2b-instruct:free", "max_tokens": 128},
                        {"provider": "groq", "model": "llama-3.1-8b-instant", "max_tokens": 256},
                    ],
                },
                "cron-classify": {
                    "description": "Simple classify",
                    "cost_cap_per_call_usd": 0.001,
                    "cost_cap_per_hour_usd": 0.05,
                    "tiers": [
                        {"provider": "openrouter", "model": "cohere/north-mini-code:free", "max_tokens": 256},
                        {"provider": "groq", "model": "llama-3.1-8b-instant", "max_tokens": 512},
                    ],
                },
            },
            "policy": {"max_tier_jumps": 2, "escalate_on": ["rate_limit", "timeout", "server_error", "cost_cap"], "telemetry_dir": "memory/research"},
        }
    return cfg

def get_group_config(cfg: dict[str, Any], group: str) -> dict[str, Any]:
    groups = cfg.get("groups", {})
    if group not in groups:
        # fallback to first available or cron-status-check
        group = next(iter(groups), "cron-status-check")
    g = groups[group].copy()
    g["name"] = group
    g.setdefault("default_max_tokens", 512)
    return g

def validate_config(cfg: dict[str, Any]) -> list[str]:
    """Basic validation. Returns list of error strings."""
    errs = []
    if "groups" not in cfg or not cfg["groups"]:
        errs.append("missing groups")
    for gname, g in cfg.get("groups", {}).items():
        if not g.get("tiers"):
            errs.append(f"group {gname} has no tiers")
        for t in g.get("tiers", []):
            if not t.get("provider") or not t.get("model"):
                errs.append(f"bad tier in {gname}")
    return errs
