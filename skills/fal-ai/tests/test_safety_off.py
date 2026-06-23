#!/usr/bin/env python3
"""Pytest suite for skills/fal-ai/safety_off.py.

Covers the required behaviors per SKILL.md §13a and the finalization plan:
- with_safety_off merge semantics (user wins, unknown passthrough, empty/None)
- SAFETY_OFF_DEFAULTS knob correctness (snapshot / per-model assertions)
- subscribe / submit / run wrappers forward to fal_client with merged args
- NO_USER_SAFETY_MODELS is non-empty and matches documented authoritative list

Run:
    python3 -m pytest skills/fal-ai/tests/ -v
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Make sibling modules importable when running via pytest from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from safety_off import (
    with_safety_off,
    subscribe,
    submit,
    run,
    SAFETY_OFF_DEFAULTS,
    NO_USER_SAFETY_MODELS,
)


# ------------------------------------------------------------------
# with_safety_off merge behavior
# ------------------------------------------------------------------

def test_with_safety_off_merges_user_wins():
    """User-provided args override defaults."""
    model = "fal-ai/flux-pro/v1.1-ultra"
    user = {"prompt": "hello", "safety_tolerance": "3"}  # explicit override
    result = with_safety_off(model, user)
    assert result["safety_tolerance"] == "3"  # user wins
    assert result["prompt"] == "hello"
    # default still present for other keys? not in this model, but structure ok
    assert "prompt" in result


def test_with_safety_off_unknown_model_passthrough():
    """Models not in SAFETY_OFF_DEFAULTS return args unchanged."""
    model = "fal-ai/some-future-model/that-does-not-exist"
    args = {"prompt": "x", "foo": 42}
    result = with_safety_off(model, args)
    assert result == args
    # also ensure no mutation of input
    assert "safety_tolerance" not in result


def test_with_safety_off_empty_args_applies_defaults():
    """Empty dict (or falsy) still receives the model defaults."""
    model = "fal-ai/flux/dev"
    result = with_safety_off(model, {})
    assert result == {"enable_safety_checker": False}

    result2 = with_safety_off(model, None)
    assert result2 == {"enable_safety_checker": False}


def test_with_safety_off_args_none_handled():
    """Explicit None for args is treated like no user args."""
    model = "fal-ai/nano-banana-2/edit"
    result = with_safety_off(model, None)
    assert result == {"safety_tolerance": "6"}


# ------------------------------------------------------------------
# SAFETY_OFF_DEFAULTS snapshot / knob assertions
# ------------------------------------------------------------------

def test_safety_off_defaults_snapshot_and_knobs():
    """All 11 models map to the documented knob values (user-facing only)."""
    assert len(SAFETY_OFF_DEFAULTS) == 11

    enable_models = {
        "fal-ai/flux/schnell",
        "fal-ai/flux/dev",
        "fal-ai/flux-2-pro",
        "fal-ai/flux-kontext-lora",
        "ideogram/v4",
        "alibaba/happy-horse/text-to-video",
    }
    tolerance_models = {
        "fal-ai/flux-pro/v1.1-ultra",
        "fal-ai/flux-pro/kontext",
        "fal-ai/nano-banana-2",
        "fal-ai/nano-banana-2/edit",
        "fal-ai/veo3",
    }
    # flux-2-pro legitimately appears under enable (it also gets tolerance)
    all_expected = enable_models | tolerance_models
    assert set(SAFETY_OFF_DEFAULTS.keys()) == all_expected

    for model, defaults in SAFETY_OFF_DEFAULTS.items():
        if "enable_safety_checker" in defaults:
            assert defaults["enable_safety_checker"] is False, f"{model} enable"
        if "safety_tolerance" in defaults:
            assert defaults["safety_tolerance"] == "6", f"{model} tolerance"


# ------------------------------------------------------------------
# Wrapper forwarding (mock fal_client)
# ------------------------------------------------------------------

def test_subscribe_forwards_to_fal_client_with_merged_args():
    model = "fal-ai/flux-pro/v1.1-ultra"
    user_args = {"prompt": "a cat", "aspect_ratio": "16:9"}

    with patch("safety_off.fal_client") as mock_fal:
        mock_fal.subscribe.return_value = {"ok": True}
        result = subscribe(model, arguments=user_args, with_logs=True)

        mock_fal.subscribe.assert_called_once()
        call_args = mock_fal.subscribe.call_args
        # wrapper does: fal_client.subscribe(model_id, arguments=merged, **kwargs)
        assert call_args.args[0] == model
        assert "arguments" in call_args.kwargs
        merged = call_args.kwargs["arguments"]
        assert merged["safety_tolerance"] == "6"
        assert merged["prompt"] == "a cat"
        assert call_args.kwargs.get("with_logs") is True
        assert result == {"ok": True}


def test_submit_and_run_forward_kwargs():
    model = "fal-ai/flux/schnell"
    user_args = {"prompt": "test"}

    with patch("safety_off.fal_client") as mock_fal:
        mock_fal.submit.return_value = MagicMock(request_id="abc123")
        mock_fal.run.return_value = {"images": []}

        h = submit(model, arguments=user_args, webhook_url="https://ex.com/hook")
        assert h.request_id == "abc123"
        call = mock_fal.submit.call_args.kwargs
        assert call["arguments"]["enable_safety_checker"] is False
        assert call["webhook_url"] == "https://ex.com/hook"

        out = run(model, arguments={"prompt": "fast"}, timeout=30)
        assert out == {"images": []}
        run_call = mock_fal.run.call_args.kwargs
        assert run_call["arguments"]["enable_safety_checker"] is False
        assert run_call["timeout"] == 30


# ------------------------------------------------------------------
# NO_USER_SAFETY_MODELS
# ------------------------------------------------------------------

def test_no_user_safety_models_nonempty_and_authoritative():
    """NO_USER_SAFETY_MODELS must be non-empty and match the documented list.

    The exact set in safety_off.py is authoritative (SKILL.md §13a will
    reference it after sync). This test guards the list itself.
    """
    assert isinstance(NO_USER_SAFETY_MODELS, (set, frozenset))
    assert len(NO_USER_SAFETY_MODELS) >= 10  # we know 18 today

    # Key members that appear in SKILL.md prose + research docs
    expected_members = {
        "krea/v2/medium/text-to-image",
        "bytedance/seedance-2.0/text-to-video",
        "fal-ai/kling-video/v3/pro/image-to-video",
        "fal-ai/minimax-music/v2.6",
        "fal-ai/elevenlabs/tts/turbo-v2.5",
        "fal-ai/whisper",
        "tripo3d/p1/image-to-3d",
    }
    assert expected_members.issubset(NO_USER_SAFETY_MODELS)

    # The list in SKILL.md §13a (after the planned edit) is derived from here.
    # No drift allowed without updating both.
