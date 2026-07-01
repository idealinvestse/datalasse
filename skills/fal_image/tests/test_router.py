"""Tests for use-case router and detection."""

import pytest

from skills.fal_image.router import (
    route_use_case, detect_use_case, get_use_case_chain, USE_CASE_CHAINS,
)


def test_all_chains_present():
    assert len(USE_CASE_CHAINS) == 11
    for chain in USE_CASE_CHAINS.values():
        assert len(chain) >= 1


def test_route_hero():
    primary = route_use_case("hero_photoreal")
    assert primary == "fal-ai/flux-2-pro"


def test_route_logo():
    p = route_use_case("logo_text_poster")
    assert "ideogram" in p or "gpt" in p


def test_auto_detect_keywords():
    assert detect_use_case("make a logo for my brand") == "logo_text_poster"
    assert detect_use_case("cute 9:16 vertical instagram story") == "social_vertical"
    assert detect_use_case("vector svg icon of a claw") == "vector_svg_icon"
    assert detect_use_case("sketch draft of a hero") == "sketch_draft_quick"
    assert detect_use_case("edit the image please, change colors") == "edit_modify"
    assert detect_use_case("upscale this to 4k") == "upscale"
    assert detect_use_case("remove the background") == "background_removal"
    assert detect_use_case("text heavy infographic poster") == "complex_text_heavy"
    assert detect_use_case("beautiful photoreal hero image") == "hero_photoreal"
    assert detect_use_case("anime style illustration set") == "illustration_anime"


def test_unknown_defaults_hero():
    assert detect_use_case("random words without keywords") == "hero_photoreal"


def test_get_chain_returns_list():
    chain = get_use_case_chain("transparent_sticker")
    assert "ideogram/v4" in chain[0]
    assert len(chain) >= 2
