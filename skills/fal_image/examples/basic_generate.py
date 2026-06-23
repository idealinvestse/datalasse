"""Basic text-to-image generation example using fal-image orchestrator."""

from skills.fal_image import generate, DEFAULT_MODEL, choose_and_generate

if __name__ == "__main__":
    print("=== Basic generation (default model) ===")
    result = generate(
        "a serene Japanese garden at dusk, cherry blossoms, soft lantern light, cinematic",
        aspect_ratio="16:9",
    )
    print("URL:", result["images"][0]["url"])

    print("\n=== Router-chosen fast generation ===")
    fast_result = choose_and_generate(
        "minimalist logo of a moss-covered stone, vector style",
        prefer_speed=True,
        budget="low",
    )
    print("URL:", fast_result["images"][0]["url"])