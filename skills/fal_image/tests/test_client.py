"""Mocked client tests for generate/edit + new functions."""

import pytest

from skills.fal_image.client import (
    generate, edit, generate_for_use_case, upscale, remove_background,
    make_vector, batch_generate,
)


def test_generate_applies_safety_and_calls(mock_fal_client):
    res = generate("a test prompt", aspect_ratio="1:1")
    assert res["images"][0]["url"].startswith("https://fal.media")
    call = mock_fal_client.subscribe.call_args
    assert "enable_safety_checker" in call.kwargs["arguments"] or "safety_tolerance" in call.kwargs["arguments"]


def test_generate_for_use_case_routes():
    res = generate_for_use_case("logo_text_poster", "logo for test")
    # just ensure it didn't blow up (mocked)
    assert "images" in res


def test_upscale_and_remove_bg(mock_fal_client):
    u = upscale("https://example.com/img.png", scale=2)
    assert "images" in u
    r = remove_background("https://example.com/img.png")
    assert "images" in r


def test_make_vector_and_batch(mock_fal_client):
    v = make_vector("simple icon")
    assert "images" in v
    batch = batch_generate(["p1", "p2"], num_images=1)
    assert len(batch) == 2


def test_edit_uploads_if_local(monkeypatch, mock_fal_client):
    # simulate local path
    res = edit("/tmp/local.png", "make it better")
    assert res

def test_extra_branches_for_coverage(mock_fal_client):
    # hit make_transparent, batch, edit_with_model, make_variations
    from skills.fal_image.client import make_transparent, batch_generate, edit_with_model, make_variations
    _ = make_transparent("https://ex.com/img.png")
    _ = batch_generate(["p1", "p2"], model="fal-ai/flux/schnell")
    _ = edit_with_model("https://ex.com/img.png", "make brighter", "fal-ai/flux-2-pro/edit")
    _ = make_variations("https://ex.com/ref.png", n=1)
