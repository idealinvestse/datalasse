"""Demonstrates the model router choosing the best model for different needs."""

from skills.fal_image.registry import choose_model, list_models

if __name__ == "__main__":
    print("=== Available editors (max_refs >= 4) ===")
    editors = list_models(feature="edit")
    for m in editors:
        if m.max_reference_images >= 4:
            print(f"  {m.model_id:35} | max_refs={m.max_reference_images}")

    print("\n=== Router decisions ===")
    print("Fast & cheap:", choose_model(prefer_speed=True, budget="low"))
    print("Best quality:", choose_model(prefer_quality=True, budget="high"))
    print("Needs editing (4 refs):", choose_model(needs_edit=True, max_refs=4))
    print("Default balanced:", choose_model())