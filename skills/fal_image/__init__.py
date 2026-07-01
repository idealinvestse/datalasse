"""fal-image — Orchestrating skill for all fal.ai image generation.

Public API:
    generate, edit, variations, choose_and_generate, generate_for_use_case,
    edit_with_model, upscale, remove_background, make_vector, make_transparent,
    batch_generate, make_variations
    get_model, list_models, choose_model, route_use_case, detect_use_case
    WorkflowResult + workflow fns
    with_safety_off
"""

from .client import (
    generate, edit, variations, choose_and_generate,
    generate_for_use_case, edit_with_model, upscale, remove_background,
    make_vector, make_transparent, make_variations, batch_generate,
)
from .registry import (
    get_model, list_models, choose_model, DEFAULT_MODEL, BEST_EDITOR,
    get_all_model_ids,
)
from .safety import with_safety_off
from .router import route_use_case, detect_use_case, get_use_case_chain, USE_CASE_CHAINS, list_use_cases
from .workflows import (
    WorkflowResult,
    sketch_to_hero, transparent_sticker, product_shot,
    logo_variations, illustration_set,
)

__all__ = [
    "generate", "edit", "variations", "choose_and_generate",
    "generate_for_use_case", "edit_with_model", "upscale", "remove_background",
    "make_vector", "make_transparent", "make_variations", "batch_generate",
    "get_model", "list_models", "choose_model", "get_all_model_ids",
    "with_safety_off",
    "DEFAULT_MODEL", "BEST_EDITOR",
    "route_use_case", "detect_use_case", "get_use_case_chain", "USE_CASE_CHAINS", "list_use_cases",
    "WorkflowResult",
    "sketch_to_hero", "transparent_sticker", "product_shot",
    "logo_variations", "illustration_set",
]