"""Image editing example using fal-image orchestrator."""

from skills.fal_image import edit, BEST_EDITOR

if __name__ == "__main__":
    # Replace with a real image URL or local path
    ref_image = "https://fal.media/files/..."  # TODO: replace with real URL

    print("=== Editing with Nano Banana 2 (multi-ref capable) ===")
    result = edit(
        image_url=ref_image,
        prompt="turn the scene into a cyberpunk night city, neon reflections, rainy",
        model=BEST_EDITOR,
        strength=0.65,
        aspect_ratio="16:9",
    )
    print("Edited URL:", result["images"][0]["url"])