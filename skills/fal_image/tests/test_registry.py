"""Tests for registry (models, filters, choose)."""

import pytest

from skills.fal_image.registry import (
    MODEL_REGISTRY, list_models, choose_model, get_model, get_all_model_ids,
    DEFAULT_MODEL,
)


def test_registry_size_and_required_fields():
    assert len(MODEL_REGISTRY) >= 24
    for mid, info in MODEL_REGISTRY.items():
        assert info.model_id == mid
        assert info.tier in ("fast", "balanced", "premium")
        assert isinstance(info.use_cases, list)
        assert info.cost_per_image_usd >= 0
        assert info.latency_seconds


def test_unique_ids():
    ids = list(MODEL_REGISTRY.keys())
    assert len(ids) == len(set(ids))


def test_list_models_filters(registry_snapshot):
    edits = list_models(feature="edit")
    assert all(m.supports_edit for m in edits)
    premiums = list_models(tier="premium")
    assert all(m.tier == "premium" for m in premiums)
    flux = list_models(family="flux")
    assert len(flux) >= 3
    # coverage for use_case filter + prefer_speed
    hero = list_models(use_case="hero_photoreal")
    assert len(hero) >= 1
    _ = choose_model(prefer_speed=True)


def test_choose_model_defaults_and_prefs():
    d = choose_model()
    assert d in MODEL_REGISTRY
    fast = choose_model(prefer_speed=True, budget="low")
    info = get_model(fast)
    assert info.tier == "fast" or "schnell" in fast or "lite" in fast
    editor = choose_model(needs_edit=True, max_refs=4)
    assert get_model(editor).supports_edit


def test_default_is_flux2_pro():
    assert "flux-2-pro" in DEFAULT_MODEL
    assert get_model(DEFAULT_MODEL) is not None


def test_get_all_model_ids():
    ids = get_all_model_ids()
    assert len(ids) >= 24
    assert DEFAULT_MODEL in ids
