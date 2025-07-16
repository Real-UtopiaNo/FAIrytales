import os
import torch
from diffusers import AutoPipelineForText2Image
from PIL import Image

os.environ['HF_HOME'] = 'D:\\huggingface'  # 强制指定所有缓存目录
os.environ['HUGGINGFACE_HUB_CACHE'] = 'D:\\huggingface\\models'  # 只指定模型缓存

def generate_image(prompt):
    pipe = AutoPipelineForText2Image.from_pretrained(
        "lykon/dreamshaper-8",
        torch_dtype=torch.float16
    ).to("cuda")
    
    image = pipe(
        prompt,
        negative_prompt="low quality, bad anatomy",
        num_inference_steps=25,
        guidance_scale=7.5
    ).images[0]
    
    return image

def save_image(image: Image, filepath: str):
    """
    保存生成的图片到指定路径
    
    Args:
        image (PIL.Image): 要保存的图片对象
        filepath (str): 保存路径
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 保存图片
        image.save(filepath)
        print(f"图片已保存到: {filepath}")
    except Exception as e:
        print(f"图片保存失败: {str(e)}")

def process_story_for_images(story_data: dict):
    """
    接收故事的结构化数据，并提取生成图片所需的信息。

    Args:
        story_data (dict): 包含故事标题和段落的字典。
    """
    if not story_data:
        print("错误：传入的故事数据为空。")
        return

    title = story_data.get("title", "untitled_story")
    parts = story_data.get("parts", [])

    print(f"--- 开始为故事 '{title}' 提取图片信息 ---")
    
    # 创建一个目录来存放图片
    output_dir = os.path.join("books", title)
    os.makedirs(output_dir, exist_ok=True)
    print(f"图片将保存在: {output_dir}")

    for i, part in enumerate(parts):
        paragraph_number = i + 1
        t2i_prompt = part.get("t2i_prompt")

        if t2i_prompt:
            print(f"\n[段落 {paragraph_number}]")
            print(f"  - 图片生成提示: {t2i_prompt}")
            
            # 生成图片
            image = generate_image(t2i_prompt)
            if image:
                # 保存图片
                image_path = os.path.join(output_dir, f"image_{paragraph_number}.png")
                save_image(image, image_path)
        else:
            print(f"\n[段落 {paragraph_number}]")
            print("  - 警告: 未找到 t2i_prompt。")

# 示例用法
if __name__ == "__main__":
    example_story = {
        "title": "小王子",
        "parts": [
            {
                "text": "一只羊在吃草",
                "t2i_prompt": "一只羊在吃草，周围是草原，童话风格"
            },
            {
                "text": "小王子每天都会清理他的星球，防止猴面包树长大...",
                "t2i_prompt": "小王子在照料小行星上的植物，水彩画风格"
            }
        ]
    }
    
    process_story_for_images(example_story)