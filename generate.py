from openai import OpenAI
import os
import json

# 初始化 OpenAI 客户端，兼容 DeepSeek API
client = OpenAI(
    api_key="sk-bb1f9a4097c74f8eb3f39cccc13be1b5",  # 或写死你的 DeepSeek 密钥
    base_url="https://api.deepseek.com/v1"
)

# 定义函数（Tool）
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_fairytales",
            "description": "Write a fairytale, which should be strictly aligned with the provided settings",
            "parameters": {
                "type": "object",
                "properties": {
                    "name_of_the_book": {"type": "string", "description": "name of the fairytales book, should be conclusive"},
                    "content_of_the_book": {"type": "string", "description": "content of the fairytales book"},
                    "visual_descriptions": {"type": "string", "description": "visual descriptions for all parts"},
                },
                "required": ["name_of_the_book", "content_of_the_book","visual_descriptions",]
            }
        }
    }
]

def generate_content_example(prompt):
    # 发起请求
    response = client.chat.completions.create(
        model="deepseek-chat",  # 或 deepseek-coder
        messages=[
            {"role": "system", "content": "You are an experienced fairytale author for children"},
            {"role": "user", "content": prompt}
        ],
        tools=tools,
        tool_choice="auto"
    )

    # 提取结果中的 JSON 参数
    tool_call = response.choices[0].message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)
    
    # 打印结构化 JSON
    # print(json.dumps(args, indent=2, ensure_ascii=False))
    print(args["name_of_the_book"])
    for i,part in enumerate(args["content_of_the_book"].split("\n")):
        print(f"Part {i+1}")
        print(part)
    for i,prompt in enumerate(args["visual_descriptions"].split("\n")):
        print(f"Prompt {i+1}")
        print(prompt)
    return args["name_of_the_book"], args["content_of_the_book"], args["visual_descriptions"]

def generate_content_vanilla(prompt):
    response = client.chat.completions.create(
        model="deepseek-chat",  # 或 deepseek-coder
        messages=[
            {"role": "system", "content": "You are an experienced fairytale author for children"},
            {"role": "user", "content": prompt}
        ],
        # tools=tools,
        tool_choice="auto"
    )
    return response.choices[0].message.content