"""Core InternalLLMRouter.

Free-first tier ladder, per-group caps, escalation (max 2 tiers), telemetry.
Reuses logic patterns from moss-router/router.js + groq_client.py .
"""
from __future__ import annotations

import os
import time
import uuid
from typing import Any

from .config import load_config, get_group_config, validate_config
from .pricing import calculate_cost
from .providers import call_provider, _is_mock
from .telemetry import append_telemetry, update_and_check_cap

class InternalLLMRouter:
    def __init__(self, config: dict[str, Any] | None = None, config_path: str | None = None):
        self.cfg = config or load_config(config_path)
        errs = validate_config(self.cfg)
        if errs:
            raise ValueError("Invalid config: " + "; ".join(errs))
        self.policy = self.cfg.get("policy", {})
        self.max_jumps = int(self.policy.get("max_tier_jumps", 2))
        self.escalate_on = set(self.policy.get("escalate_on", ["rate_limit", "timeout", "server_error", "cost_cap"]))

    def get_group(self, name: str) -> dict[str, Any]:
        return get_group_config(self.cfg, name)

    def select_tier_and_provider(self, group_cfg: dict[str, Any], tier_index: int = 0) -> dict[str, Any]:
        tiers = group_cfg.get("tiers", [])
        if not tiers:
            raise ValueError("no tiers")
        idx = min(tier_index, len(tiers) - 1)
        t = tiers[idx]
        return {
            "tier_index": idx,
            "provider": t["provider"],
            "model": t["model"],
            "max_tokens": t.get("max_tokens") or group_cfg.get("default_max_tokens", 512),
            "max_cost_usd": t.get("max_cost_usd"),
        }

    def _classify_error(self, err: Exception) -> str:
        msg = str(err).lower()
        if "rate" in msg or "429" in msg:
            return "rate_limit"
        if "timeout" in msg:
            return "timeout"
        if "5" in msg[:3] or "server" in msg or "internal" in msg:
            return "server_error"
        return "other"

    def execute(
        self,
        group: str,
        prompt: str,
        system: str | None = None,
        max_tokens: int | None = None,
        extra: dict | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Main entry. Returns (content, meta)."""
        group_cfg = self.get_group(group)
        per_call_cap = float(group_cfg.get("cost_cap_per_call_usd", 0.001))
        per_hour_cap = float(group_cfg.get("cost_cap_per_hour_usd", 0.05))
        default_mt = group_cfg.get("default_max_tokens", 512)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        tier_idx = 0
        attempts = 0
        last_err: Exception | None = None
        used_provider = ""
        used_model = ""
        used_cost = 0.0
        meta: dict[str, Any] = {}

        while tier_idx <= self.max_jumps:
            sel = self.select_tier_and_provider(group_cfg, tier_idx)
            mt = max_tokens or sel["max_tokens"]
            prov = sel["provider"]
            mod = sel["model"]
            used_provider = prov
            used_model = mod
            attempts += 1

            # per-call guard
            est_max = sel.get("max_cost_usd") or per_call_cap
            if est_max > per_call_cap:
                # escalate early if tier too expensive for cap
                tier_idx += 1
                continue

            try:
                # check hour cap before call (pre-emptive)
                allowed, _ = update_and_check_cap(group, 0.0, per_hour_cap)  # just touch
                if not allowed:
                    raise RuntimeError("hourly cost cap exceeded pre-call")

                res = call_provider(prov, mod, messages, mt, self.cfg)
                content = res["content"]
                usage = res["usage"]
                cost = calculate_cost(usage, mod)
                used_cost = cost

                # post call caps
                if cost > per_call_cap:
                    append_telemetry({
                        "task_group": group,
                        "tier_index": tier_idx,
                        "provider": prov,
                        "model": mod,
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "cost_usd": cost,
                        "latency_ms": res.get("latency_ms", 0),
                        "success": False,
                        "error_class": "cost_cap",
                    }, self.cfg)
                    tier_idx += 1
                    continue

                allowed, spent = update_and_check_cap(group, cost, per_hour_cap)
                if not allowed:
                    raise RuntimeError(f"hourly cost cap exceeded: {spent} > {per_hour_cap}")

                meta = {
                    "group": group,
                    "tier_index": tier_idx,
                    "provider": prov,
                    "model": mod,
                    "cost_usd": cost,
                    "latency_ms": res.get("latency_ms", 0),
                    "usage": usage,
                    "mock": _is_mock(),
                    "attempts": attempts,
                }
                append_telemetry({
                    "task_group": group,
                    "tier_index": tier_idx,
                    "provider": prov,
                    "model": mod,
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "cost_usd": cost,
                    "latency_ms": res.get("latency_ms", 0),
                    "success": True,
                    "error_class": None,
                    "call_id": str(uuid.uuid4())[:8],
                }, self.cfg)
                return content, meta

            except Exception as e:
                last_err = e
                err_class = self._classify_error(e)
                cost = 0.0  # on error
                append_telemetry({
                    "task_group": group,
                    "tier_index": tier_idx,
                    "provider": prov,
                    "model": mod,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "cost_usd": 0.0,
                    "latency_ms": 0,
                    "success": False,
                    "error_class": err_class,
                    "call_id": str(uuid.uuid4())[:8],
                }, self.cfg)
                if err_class in self.escalate_on or err_class == "cost_cap":
                    tier_idx += 1
                    continue
                # non-escalate error
                break

        # exhausted
        raise RuntimeError(f"all tiers exhausted for {group} after {attempts} attempts. last={last_err}") from last_err

def get_router(config_path: str | None = None) -> InternalLLMRouter:
    return InternalLLMRouter(config_path=config_path)

def call_group(
    group: str,
    prompt: str,
    system: str | None = None,
    max_tokens: int | None = None,
    config_path: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Convenience."""
    r = get_router(config_path)
    return r.execute(group, prompt, system=system, max_tokens=max_tokens)
