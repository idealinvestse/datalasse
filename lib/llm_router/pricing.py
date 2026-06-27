"""Pricing for internal router.

Seeded from memory/research/*/prices-2026-06-27.json (OpenRouter/Groq 2026-06-27).
Free models have 0 cost. Minimal subset + defaults for used groups.
"""
from __future__ import annotations

from typing import Any

# Prices per 1M tokens (input, output). 0 for free/:free .
PRICING: dict[str, tuple[float, float]] = {
    # Free OR (from table 2026-06-27)
    "liquid/lfm-2.5-1.2b-instruct:free": (0.0, 0.0),
    "liquid/lfm-2.5-1.2b-thinking:free": (0.0, 0.0),
    "cohere/north-mini-code:free": (0.0, 0.0),
    "google/gemma-4-31b-it:free": (0.0, 0.0),
    "meta-llama/llama-3.2-3b-instruct:free": (0.0, 0.0),
    "openrouter/free": (0.0, 0.0),
    # Groq free-ish / compound (prices null -> treat as 0 for router)
    "groq/compound": (0.0, 0.0),
    "groq/compound-mini": (0.0, 0.0),
    # Groq nano/eco (from groq prices)
    "llama-3.1-8b-instant": (0.05, 0.08),
    "openai/gpt-oss-20b": (0.075, 0.30),
    "llama-3.3-70b-versatile": (0.59, 0.79),
    "openai/gpt-oss-120b": (0.15, 0.60),
    # Cheap paid OR (from prices)
    "inclusionai/ling-2.6-flash": (0.01, 0.03),
    # Others used in groups (approx from research)
    "openrouter/deepseek/deepseek-v4-pro": (0.30, 0.90),  # approx
    "openrouter/qwen/qwen3.6-35b-a3b": (0.14, 1.00),
    "qwen/qwen3-coder-30b-a3b-instruct": (0.07, 0.27),
    "openrouter/x-ai/grok-4.3": (1.25, 5.00),  # rough, not cheapest
    "openrouter/qwen/qwen3-next-80b-a3b-thinking": (0.10, 0.80),
    "openrouter/anthropic/claude-sonnet-4.6": (3.00, 15.00),
    "openrouter/x-ai/grok-4.20": (1.25, 5.00),
    "default": (0.50, 1.50),
}

def get_price(model: str) -> tuple[float, float]:
    """Return (input_per_1m, output_per_1m) for model. Case-insensitive prefix match."""
    if not model:
        return PRICING["default"]
    m = model.lower().strip()
    if m in PRICING:
        return PRICING[m]
    for k, p in PRICING.items():
        if k in m or m in k or k.split("/")[-1] in m:
            return p
    return PRICING["default"]

def calculate_cost(usage: Any, model: str) -> float:
    """Calculate USD from usage (prompt_tokens, completion_tokens) or dict."""
    if usage is None:
        return 0.0
    try:
        if hasattr(usage, "prompt_tokens"):
            pt = getattr(usage, "prompt_tokens", 0) or 0
            ct = getattr(usage, "completion_tokens", 0) or 0
        elif isinstance(usage, dict):
            pt = usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0
            ct = usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0
        else:
            pt = int(getattr(usage, "prompt_tokens", 0) or 0)
            ct = int(getattr(usage, "completion_tokens", 0) or 0)
        pin, pout = get_price(model)
        cost = (pt / 1_000_000.0 * pin) + (ct / 1_000_000.0 * pout)
        return round(cost, 8)
    except Exception:
        return 0.0
