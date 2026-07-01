"""Mocked workflow tests."""

import pytest

from skills.fal_image.workflows import (
    sketch_to_hero, transparent_sticker, product_shot,
    logo_variations, illustration_set, WorkflowResult,
)


def test_sketch_to_hero_returns_result():
    wr = sketch_to_hero("test prompt")
    assert isinstance(wr, WorkflowResult)
    assert wr.primary_url
    assert wr.total_cost_usd > 0
    assert len(wr.models_used) >= 2
    assert "flux" in wr.models_used[0] or "schnell" in wr.models_used[0]


def test_transparent_and_product():
    wr = transparent_sticker("sticker prompt")
    assert wr.primary_url
    wr2 = product_shot("product on table")
    assert wr2.total_cost_usd > 0


def test_variations_and_set():
    wr = logo_variations("TestBrand", n=2)
    assert len(wr.output_urls) >= 1
    wr = illustration_set("anime forest", n=3)
    assert len(wr.models_used) >= 1
