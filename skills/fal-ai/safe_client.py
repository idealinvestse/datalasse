#!/usr/bin/env python3
"""Drop-in safety-off client (thin re-export).

This module fulfills the contract documented in SKILL.md §13a:
a convenient drop-in replacement for `fal_client` that always
applies the workspace safety-off defaults (`enable_safety_checker=False`
or `safety_tolerance="6"` where supported).

All real logic lives in `safety_off.py` (the single source of truth for
SAFETY_OFF_DEFAULTS, NO_USER_SAFETY_MODELS, with_safety_off, subscribe,
submit, and run).

Usage (as promised in SKILL.md):
    from safe_client import subscribe, submit, run, with_safety_off

    result = subscribe("fal-ai/flux-pro/v1.1-ultra", arguments={"prompt": "..."})
"""

from safety_off import (
    subscribe,
    submit,
    run,
    with_safety_off,
    SAFETY_OFF_DEFAULTS,
    NO_USER_SAFETY_MODELS,
)

__all__ = [
    "subscribe",
    "submit",
    "run",
    "with_safety_off",
    "SAFETY_OFF_DEFAULTS",
    "NO_USER_SAFETY_MODELS",
]
