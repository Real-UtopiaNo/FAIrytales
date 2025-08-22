import json
from llm_api import generate_content

SAFETY_CHECK_SYSTEM_PROMPT = """
你是一位经验丰富的儿童内容安全审核专家。你的唯一任务是评估给定的文本是否完全适合5-8岁的儿童。
你需要检查以下几点：
1.  **暴力与血腥**：绝对不允许出现任何形式的暴力、血腥、残忍或令人不适的描写。
2.  **色情与不当内容**：绝对不允许出现任何色情、性暗示或不适合儿童的成人话题。
3.  **恐怖与惊悚**：不允许出现可能导致儿童恐惧、焦虑或做噩梦的恐怖、惊悚元素。
4.  **负面价值观**：不允许宣扬自私、欺骗、仇恨、歧视或任何其他负面的价值观。

你的回答必须是一个JSON对象，且只包含两个字段：
-   `"is_safe"`: 一个布尔值，`true` 表示内容安全，`false` 表示内容不安全。
-   `"reason"`: 一段简短的字符串，解释你的判断依据。如果安全，可以说明"内容健康，适合儿童。"
"""

PROMPT_CHECK_SYSTEM_PROMPT = """
你是一位内容策略专家，负责确保用户生成儿童故事的请求是善意且安全的。
你的任务是分析用户的请求（Prompt），判断其意图是否适合为5-8岁的儿童创作故事。
你需要检查以下几点：
1.  **不当主题**：请求是否涉及暴力、战争、死亡、色情、恐怖、政治或其他任何成人化或有争议的话题？
2.  **负面意图**：请求是否暗示了要创作一个宣扬仇恨、歧视、霸凌或其他负面价值观的故事？

你的回答必须是一个JSON对象，且只包含两个字段：
-   `"is_safe"`: 一个布尔值，`true` 表示请求的意图是安全的，`false` 表示不安全。
-   `"reason"`: 一段简短的字符串，解释你的判断依据。
"""

def _perform_safety_check(text_to_check: str, system_prompt: str) -> (bool, str):
    """一个通用的安全检查辅助函数"""
    try:
        response_text = generate_content(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text_to_check}
            ],
            is_json=True,
            model_type='safety_check'
        )
        
        result_json = json.loads(response_text)
        is_safe = result_json.get("is_safe", False)
        reason = result_json.get("reason", "No reason provided.")
        return is_safe, reason

    except Exception as e:
        print(f"An error occurred during safety check: {e}")
        return False, str(e)

def is_content_safe(story_data: dict) -> bool:
    """
    使用LLM评估生成的故事内容的安全性。
    """
    if not story_data or not story_data.get("story_parts"):
        return True

    full_story_text = story_data.get("title", "") + "\n"
    for part in story_data["story_parts"]:
        full_story_text += part.get("content", "") + "\n"
    
    print("\n--- Performing safety check on generated CONTENT ---")
    is_safe, reason = _perform_safety_check(full_story_text, SAFETY_CHECK_SYSTEM_PROMPT)

    if is_safe:
        print(f"--- Content Safety Check Passed --- Reason: {reason}")
        return True
    else:
        print(f"--- Content Safety Check Failed --- Reason: {reason}")
        print("Will attempt to regenerate the story.")
        return False

def is_prompt_safe(prompt_text: str) -> bool:
    """
    使用LLM评估输入Prompt的安全性。
    """
    print("\n--- Performing safety check on user PROMPT ---")
    is_safe, reason = _perform_safety_check(prompt_text, PROMPT_CHECK_SYSTEM_PROMPT)
    
    if is_safe:
        print(f"--- Prompt Safety Check Passed --- Reason: {reason}")
        return True
    else:
        print(f"--- Prompt Safety Check Failed --- Reason: {reason}")
        return False
