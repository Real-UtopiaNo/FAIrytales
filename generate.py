import re
import json
import os
# from openai import OpenAI #不再需要直接导入
from safety_checker import is_content_safe, is_prompt_safe # 导入两种安全检查函数
from llm_api import generate_content_with_tools, generate_content

# # 初始化 OpenAI 客户端，兼容 DeepSeek API（已移至 llm_api.py）
# client = OpenAI(
#     api_key="sk-38195cc9744a44e385c221cb7b865ecc",  # 或写死你的 DeepSeek 密钥
#     base_url="https://api.deepseek.com/v1"
# )

# --- 方法一：Function Calling (首选) ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "create_fairytale",
            "description": "Creates a multi-part fairytale story with a title, and for each part, provides content and a visual description for an image.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title of the fairytale, based on the user's prompt."
                    },
                    "story_parts": {
                        "type": "array",
                        "description": "An array of story parts, each with its content and an image prompt.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "part_number": {"type": "integer", "description": "The sequence number of this part."},
                                "content": {"type": "string", "description": "The text content for this part."},
                                "t2i_prompt": {"type": "string", "description": "A prompt for generating an illustration for this part."},
                                "width": {"type": "integer", "description": "Appropriate Width for the image,each part can be different."},
                                "height": {"type": "integer", "description": "Appropriate Height for the image,,each part can be different."}
                            },
                            "required": ["part_number", "content", "t2i_prompt", "width", "height"]
                        }
                    }
                },
                "required": ["title", "story_parts"]
            }
        }
    }
]


# --- 方法二：正则表达式解析 (备用) ---
def parse_story_with_regex(text_blob: str, default_width: int = 512, default_height: int = 512):
    """
    使用正则表达式从LLM返回的原始文本中解析出结构化的故事数据。
    """
    print("--- Attempting to parse with Regex ---")
    pattern = re.compile(r"第(\d+)段：\s*内容：(.*?)\s*图片提示词：(.*?)(?=\s*第\d+段：|$)", re.DOTALL)
    matches = pattern.findall(text_blob)
    
    story_parts = []
    if not matches:
        print("Warning: Regex did not find any matches.")
        return None

    for match in matches:
        part_number, content, image_prompt = match
        story_parts.append({
            "part_number": int(part_number.strip()),
            "content": content.strip(),
            "t2i_prompt": image_prompt.strip(),
            "width": default_width,  # Set the default width
            "height": default_height  # Set the default height
        })
    
    # 尝试从文本第一行提取标题
    title_match = re.search(r"标题：(.*?)\n", text_blob)
    title = title_match.group(1).strip() if title_match else "Story Title (Parsed by Regex)"
    
    return {"title": title, "story_parts": story_parts}


# --- 统一的生成和解析函数 ---
def generate_and_parse_story(prompt: str, max_retries: int = 3, default_width: int = 512, default_height: int = 512):
    """
    增加了输入Prompt检查、内容安全审核和重试机制。
    """
    # 1. 在所有操作开始前，首先检查输入Prompt的安全性
    if not is_prompt_safe(prompt):
        # 如果输入不安全，直接终止，不进行任何生成尝试
        print("\n--- Input prompt is deemed unsafe. Aborting generation. ---")
        return None

    system_prompt = """You are a helpful fairytale author. You must create content that is strictly appropriate for young children (ages 5-8).
The story must be positive, gentle, and free of any scary, violent, sexual, or otherwise inappropriate themes.
Prioritize using the `create_fairytale` function. If you cannot, fall back to providing a raw text response in the requested format."""

    for attempt in range(max_retries):
        print(f"\n--- Story Generation Attempt {attempt + 1} of {max_retries} ---")
        
        print("--- Generating story with the following prompt ---")
        print(prompt)
        print("\n--- Calling LLM with Function Calling enabled ---")
        
        try:
            message = generate_content_with_tools(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                tools=tools
            )

            structured_story = None
            
            # 优先处理 Function Calling
            if message.tool_calls:
                print("--- Success: LLM used Function Calling! ---")
                tool_call = message.tool_calls[0]
                if tool_call.function.name == 'create_fairytale':
                    structured_story = json.loads(tool_call.function.arguments)
                    # 确保 width 和 height 存在
                    for part in structured_story.get("story_parts", []):
                        part["width"] = part.get("width", default_width)
                        part["height"] = part.get("height", default_height)
            
            # 如果没有 Function Calling，则尝试 Regex 解析
            elif message.content:
                print("--- Fallback: LLM did not use Function Calling. ---")
                raw_text = message.content
                structured_story = parse_story_with_regex(raw_text, default_width, default_height)
            
            # 对成功解析出的故事进行安全检查
            if structured_story:
                if is_content_safe(structured_story):
                    print("\n--- Story has been generated and passed safety checks. ---")
                    print(json.dumps(structured_story, indent=2, ensure_ascii=False))
                    
                    # 在这里自动保存文件
                    save_success = save_story_to_files(structured_story)
                    if save_success:
                        print("\n--- 故事内容已成功保存到文件 ---")
                    else:
                        print("\n--- 保存故事内容时出错 ---")

                    return structured_story
                else:
                    # 内容不安全，继续下一次尝试
                    continue
            
        except Exception as e:
            print(f"An error occurred during story generation: {e}")
            # 发生异常时，也继续下一次尝试
            continue

    # 如果所有尝试都失败了
    print(f"\n--- Failed to generate a safe and valid story after {max_retries} attempts. ---")
    return None

def save_story_to_files(story_data, base_path="books"):
    """
    将每段的完整原始数据直接保存到txt文件，不做任何提取或格式化
    """
    if not story_data:
        print("错误：没有可保存的故事数据")
        return False

    title = story_data.get("title", "未命名故事")
    story_parts = story_data.get("story_parts", [])

    # 创建以故事标题命名的文件夹
    book_folder = os.path.join(base_path, title)
    os.makedirs(book_folder, exist_ok=True)
    
    # 保存每段的完整原始数据
    for part in story_parts:
        part_number = part.get("part_number", 1)
        
        # 创建段落文件名
        filename = f"part{part_number}_完整数据.txt"
        filepath = os.path.join(book_folder, filename)
        
        # 直接保存原始数据，不做任何提取
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(part, f, ensure_ascii=False, indent=2)
            print(f"已保存段落 {part_number} 的完整数据到：{filepath}")
        except Exception as e:
            print(f"保存段落 {part_number} 时出错：{e}")
            return False
    
    # 保存整个故事的完整原始数据
    full_filename = f"完整故事数据.json"
    full_filepath = os.path.join(book_folder, full_filename)
    
    try:
        with open(full_filepath, 'w', encoding='utf-8') as f:
            json.dump(story_data, f, ensure_ascii=False, indent=2)
        print(f"已保存完整故事数据到：{full_filepath}")
    except Exception as e:
        print(f"保存完整故事数据时出错：{e}")
        return False
    
    return True

# Example usage
if __name__ == "__main__":
    # 需要先加载llm配置
    import llm_api
    llm_api.load_config()

    prompt = "Please generate a fairytale story about a boy and a bird with image prompts for each part."
    
    # Generate and parse the story with width and height for each part
    structured_story = generate_and_parse_story(prompt)

    if structured_story:
        # 此时文件已在函数内部自动保存
        print("\n--- Story generation and saving process complete. ---")
        # 打印段落信息
        for part in structured_story.get("story_parts", []):
            print(f"Part {part['part_number']} - Width: {part['width']}, Height: {part['height']}")
    else:
        print("--- Failed to generate and parse the story ---")
