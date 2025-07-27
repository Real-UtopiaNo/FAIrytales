import os
import torch
from diffusers import AutoPipelineForText2Image
from PIL import Image
from typing import Dict, List, Optional, Any
# Translation functionality removed - handled in main script

DEFAULT_MODEL_ID = "lykon/dreamshaper-8"
DEFAULT_DEVICE = "cpu"  # change to "cpu" if no GPU
DEFAULT_WIDTH = 512
DEFAULT_HEIGHT = 512

# Global pipeline cache so we don't re-download / re-load for every image.
_PIPELINE = None

# Load pipeline function
def load_pipeline(
    model_id: str = DEFAULT_MODEL_ID,
    device: str = DEFAULT_DEVICE,
    torch_dtype: torch.dtype = torch.float32,
    cache_dir: Optional[str] = None,
) -> AutoPipelineForText2Image:
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
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        image.save(filepath)
        print(f"Image saved to: {filepath}")
    except Exception as e:
        print(f"Failed to save image: {e}")


def process_story_for_images(
    story_data: Dict[str, Any],
    *,
    default_width: int = DEFAULT_WIDTH,
    default_height: int = DEFAULT_HEIGHT,
    output_root: str = "books",
    **gen_overrides: Any,
) -> List[str]:
    if not story_data:
        print("Error: no story data provided.")
        return []

    title = story_data.get("title", "untitled_story")
    parts = story_data.get("story_parts", [])

    print(f"--- Generating images for story '{title}' ---")

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

# --- Helper functions for translation ---
def is_english(text: str) -> bool:
    """Check if a string is in English."""
    return all(ord(c) < 128 for c in text)

def translate_to_english(text: str) -> str:
    """Translation is handled in main script, return original text."""
    return text  # Translation handled elsewhere

# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    structured_story = {
        "title": "壮壮的奇幻冒险",
        "story_parts": [
            {
                "part_number": 1,
                "content": "在一个氤氲着晨雾的小村庄里，住着一个名叫壮壮的小男孩。他每天都会去森林里玩耍，和一只名叫吱吱的小鸟做朋友。吱吱的歌声清脆悦耳，为森林带来了欢声笑语。",
                "t2i_prompt": "一个小男孩和一只小鸟在晨雾弥漫的森林里玩耍。"
            },
            # More parts go here...
        ],
    }

    # Translate any non-English prompts
    print("\n--- Ensuring all image prompts are in English ---")
    for part in structured_story.get("story_parts", []):
        t2i_prompt = part.get("t2i_prompt")
        if t2i_prompt and not is_english(t2i_prompt):  # 检查是否是英文
            print(f"Converting prompt to English: {t2i_prompt}")
            part["t2i_prompt"] = translate_to_english(t2i_prompt)

    # Generate images for the story
    process_story_for_images(structured_story)
