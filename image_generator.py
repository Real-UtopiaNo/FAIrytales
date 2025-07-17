import os
import torch
from diffusers import AutoPipelineForText2Image
from PIL import Image
from typing import Dict, List, Optional, Any


DEFAULT_MODEL_ID = "lykon/dreamshaper-8"
DEFAULT_DEVICE = "cuda"  # change to "cpu" if no GPU
DEFAULT_WIDTH = 512
DEFAULT_HEIGHT = 512

# Global pipeline cache so we don't re-download / re-load for every image.
_PIPELINE = None


def load_pipeline(
    model_id: str = DEFAULT_MODEL_ID,
    device: str = DEFAULT_DEVICE,
    torch_dtype: torch.dtype = torch.float16,
    cache_dir: Optional[str] = None,
) -> AutoPipelineForText2Image:
    """Load (and memoize) the diffusion pipeline.

    Parameters
    ----------
    model_id:
        Hugging Face model repo id.
    device:
        "cuda" or "cpu".
    torch_dtype:
        torch datatype to load weights (fp16 saves memory on GPU).
    cache_dir:
        Optional explicit cache directory; useful to avoid permission errors.
    """
    global _PIPELINE
    if _PIPELINE is None:
        _PIPELINE = AutoPipelineForText2Image.from_pretrained(
            model_id,
            torch_dtype=torch_dtype,
            cache_dir=cache_dir,
        ).to(device)
    return _PIPELINE


def generate_image(
    prompt: str,
    *,
    negative_prompt: str = "low quality, bad anatomy",
    num_inference_steps: int = 25,
    guidance_scale: float = 7.5,
    width: Optional[int] = 512,
    height: Optional[int] = 512,
    pipeline: Optional[AutoPipelineForText2Image] = None,
) -> Image.Image:
    """Generate an image from a text prompt.

    width / height must be multiples of 8 (most SD models want multiples of 64
    for best results; the pipeline will usually pad internally but it's good to
    respect that). If omitted, defaults are used.
    """
    if pipeline is None:
        pipeline = load_pipeline()

    gen_kwargs: Dict[str, Any] = dict(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=num_inference_steps,
        guidance_scale=guidance_scale,
    )
    if width is not None:
        gen_kwargs["width"] = width
    if height is not None:
        gen_kwargs["height"] = height

    result = pipeline(**gen_kwargs)
    return result.images[0]


def save_image(image: Image.Image, filepath: str) -> None:
    """Save a PIL image to the given path, creating parent dirs if needed."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        image.save(filepath)
        print(f"Image saved to: {filepath}")
    except Exception as e:  # broad catch so we can see what went wrong
        print(f"Failed to save image: {e}")


def process_story_for_images(
    story_data: Dict[str, Any],
    *,
    default_width: int = DEFAULT_WIDTH,
    default_height: int = DEFAULT_HEIGHT,
    output_root: str = "books",
    **gen_overrides: Any,
) -> List[str]:
    """Generate and save images for each part of a structured story.

    Story format (minimal):
    {
        "title": "The Little Prince",
        "parts": [
            {"t2i_prompt": "A sheep is eating grass.", "width": 512, "height": 512},
            {"t2i_prompt": "The Little Prince tending to his asteroid garden, watercolor style", "width": 768, "height": 512},
            ...
        ]
    }

    Returns a list of saved image file paths.
    """
    if not story_data:
        print("Error: no story data provided.")
        return []

    title = story_data.get("title", "untitled_story")
    parts = story_data.get("parts", [])

    print(f"--- Generating images for story '{title}' ---")

    # Create output directory for this story
    output_dir = os.path.join(output_root, title)
    os.makedirs(output_dir, exist_ok=True)
    print(f"Images will be saved under: {output_dir}")

    pipeline = load_pipeline(**{k: v for k, v in gen_overrides.items() if k in {"model_id", "device", "torch_dtype", "cache_dir"}})

    saved_paths: List[str] = []

    for i, part in enumerate(parts):
        idx = i + 1
        t2i_prompt = part.get("t2i_prompt")
        if not t2i_prompt:
            print(f"[Part {idx}] Warning: no t2i_prompt found; skipping.")
            continue

        # Allow per-part width/height override
        w = part.get("width", default_width)
        h = part.get("height", default_height)

        print(f"\n[Part {idx}] Prompt: {t2i_prompt}")
        print(f"[Part {idx}] Size: {w}x{h}")

        try:
            image = generate_image(
                t2i_prompt,
                width=w,
                height=h,
                pipeline=pipeline,
            )
        except Exception as e:
            print(f"[Part {idx}] Generation failed: {e}")
            continue

        image_path = os.path.join(output_dir, f"image_{idx}.png")
        save_image(image, image_path)
        saved_paths.append(image_path)

    print("\nDone.")
    return saved_paths


# -----------------------------------------------------------------------------
# Example usage
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    example_story = {
        "title": "The Little Prince",
        "parts": [
            {
                "t2i_prompt": "A sheep is eating grass.",
                "width": 512,
                "height": 512,
            },
            {
                "t2i_prompt": "The Little Prince tending to his asteroid garden, watercolor style.",
                "width": 768,
                "height": 512,
            },
        ],
    }


    process_story_for_images(example_story)
