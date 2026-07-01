"""Safety-off application tests for registry models."""

import os
import pytest

from skills.fal_image.safety import with_safety_off
from skills.fal_image.registry import list_models, get_model
# Note: fal-ai safety is dynamically loaded; we test via the re-export
# SAFETY_OFF_DEFAULTS is re-exported via fal_image.safety
try:
    from skills.fal_image.safety import SAFETY_OFF_DEFAULTS
except Exception:
    SAFETY_OFF_DEFAULTS = {}  # safe fallback for test env without direct fal-ai


def test_safety_off_applied_for_known_models():
    # flux-2-pro should get checker + tolerance
    args = with_safety_off("fal-ai/flux-2-pro", {"prompt": "test"})
    assert args.get("enable_safety_checker") is False
    assert args.get("safety_tolerance") == "6"

    # ideogram
    args = with_safety_off("ideogram/v4", {"prompt": "logo"})
    assert args.get("enable_safety_checker") is False

    # nano
    args = with_safety_off("fal-ai/nano-banana-2", {})
    assert args.get("safety_tolerance") == "6"


def test_unknown_model_passthrough():
    args = {"prompt": "x", "foo": 1}
    out = with_safety_off("fal-ai/unknown-future-model", args)
    assert out == args


def test_user_wins():
    args = with_safety_off("fal-ai/flux-2-pro", {"safety_tolerance": "2"})
    assert args["safety_tolerance"] == "2"  # user override


def test_all_registry_models_have_safety_when_expected():
    # Only test models known to be in the canonical SAFETY_OFF_DEFAULTS
    known = ["fal-ai/flux-2-pro", "fal-ai/flux/schnell", "fal-ai/flux/dev", "ideogram/v4", "fal-ai/nano-banana-2"]
    for mid in known:
        info = get_model(mid)
        if info and info.safety_param:
            out = with_safety_off(mid, {"prompt": "t"})
            if info.safety_param == "enable_safety_checker":
                assert out.get("enable_safety_checker") is False
            if info.safety_param == "safety_tolerance":
                assert out.get("safety_tolerance") == "6"
