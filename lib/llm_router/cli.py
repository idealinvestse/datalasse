"""CLI for internal router.

python -m lib.llm_router.cli --group=... --prompt=... [--dry-run] [--json]
Used by bin/llm-call .
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# make runnable as module or direct
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.llm_router.router import get_router, call_group  # type: ignore
from lib.llm_router.config import load_config  # type: ignore
from lib.llm_router.telemetry import daily_rollup  # type: ignore

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Internal LLM Router CLI (Phase 1)")
    p.add_argument("--group", required=False, help="task group name e.g. cron-status-check")
    p.add_argument("--prompt", required=False, help="user prompt text")
    p.add_argument("--system", default=None, help="optional system prompt")
    p.add_argument("--max-tokens", type=int, default=None)
    p.add_argument("--temperature", type=float, default=None, help="sampling temperature (default 0.2)")
    p.add_argument("--model", default=None, help="optional explicit model override (uses group policy for caps/telemetry)")
    p.add_argument("--dry-run", action="store_true", help="show selection + est cost, no call")
    p.add_argument("--json", action="store_true", help="output json")
    p.add_argument("--config", default=None, help="path to config json")
    p.add_argument("--rollup", action="store_true", help="print today's rollup and exit")
    args = p.parse_args(argv)

    if args.rollup:
        r = daily_rollup()
        print(json.dumps(r, indent=2))
        return 0

    cfg = load_config(args.config)
    groups = list(cfg.get("groups", {}).keys())
    if args.group and args.group not in groups:
        print(f"ERROR: unknown group '{args.group}'. Known: {groups}", file=sys.stderr)
        return 2

    gcfg = cfg["groups"][args.group]
    # pick first tier for dry-run est
    t0 = gcfg["tiers"][0]
    model0 = t0["model"]
    from lib.llm_router.pricing import get_price, calculate_cost  # type: ignore
    pin, pout = get_price(model0)
    est = ( (len(args.prompt) // 4) * pin + 64 * pout ) / 1_000_000.0
    est = round(est, 8)

    if args.dry_run:
        out = {
            "group": args.group,
            "selected_tier": 0,
            "provider": t0["provider"],
            "model": model0,
            "est_cost_usd": est,
            "max_tokens": t0.get("max_tokens") or gcfg.get("default_max_tokens", 512),
            "dry_run": True,
            "mock": os.getenv("MOCK") == "1" or os.getenv("INTERNAL_ROUTER_MOCK") == "1",
        }
        if args.json:
            print(json.dumps(out))
        else:
            print(f"DRY-RUN group={args.group} tier0={t0['provider']}/{model0} est_cost=${est} max_tokens={out['max_tokens']}")
        return 0

    try:
        content, meta = call_group(
            args.group,
            args.prompt,
            system=args.system,
            max_tokens=args.max_tokens,
            config_path=args.config,
            temperature=args.temperature,
            model_override=args.model,
        )
        meta["content_preview"] = (content or "")[:200]
        if args.json:
            print(json.dumps({"content": content, "meta": meta}, ensure_ascii=False))
        else:
            print(f"[{meta['provider']}/{meta['model']} tier={meta['tier_index']} cost=${meta['cost_usd']}]")
            print(content)
        return 0
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
