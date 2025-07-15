import re
import json
from openai import OpenAI


# 初始化 OpenAI 客户端，兼容 DeepSeek API
client = OpenAI(
    api_key="sk-38195cc9744a44e385c221cb7b865ecc",  # 或写死你的 DeepSeek 密钥
    base_url="https://api.deepseek.com/v1"
)

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
                                "image_prompt": {"type": "string", "description": "A prompt for generating an illustration for this part."}
                            },
                            "required": ["part_number", "content", "image_prompt"]
                        }
                    }
                },
                "required": ["title", "story_parts"]
            }
        }
    }
]

# --- 方法二：正则表达式解析 (备用) ---
def parse_story_with_regex(text_blob: str):
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
            "image_prompt": image_prompt.strip()
        })
    
    # 尝试从文本第一行提取标题
    title_match = re.search(r"标题：(.*?)\n", text_blob)
    title = title_match.group(1).strip() if title_match else "Story Title (Parsed by Regex)"
    
    return {"title": title, "story_parts": story_parts}


# --- 统一的生成和解析函数 ---
def generate_and_parse_story(prompt: str):
    """
    首选Function Calling，如果失败则自动降级到Regex解析。
    """
    print("--- Calling LLM with Function Calling enabled ---")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful fairytale author. Prioritize using the `create_fairytale` function. If you cannot, fall back to providing a raw text response in the requested format."},
            {"role": "user", "content": prompt}
        ],
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message
    
    # 优先处理 Function Calling
    if message.tool_calls:
        print("--- Success: LLM used Function Calling! ---")
        tool_call = message.tool_calls[0]
        if tool_call.function.name == 'create_fairytale':
            return json.loads(tool_call.function.arguments)
    
    # 如果没有 Function Calling，则尝试 Regex 解析
    print("--- Fallback: LLM did not use Function Calling. ---")
    raw_text = message.content
    if raw_text:
        return parse_story_with_regex(raw_text)
        
    # 如果两种方法都失败
    print("--- Error: Both Function Calling and Regex parsing failed. ---")
    return None