# sk-bb1f9a4097c74f8eb3f39cccc13be1b5
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
            "name": "get_person_info",
            "description": "返回一个人的姓名、年龄和城市信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "人的姓名"},
                    "age": {"type": "integer", "description": "年龄"},
                    "city": {"type": "string", "description": "所在城市"},
                },
                "required": ["name", "age", "city"]
            }
        }
    }
]

# 发起请求
response = client.chat.completions.create(
    model="deepseek-chat",  # 或 deepseek-coder
    messages=[
        {"role": "user", "content": "请随机给我一个人的姓名、年龄和所在城市"}
    ],
    tools=tools,
    tool_choice="auto"
)

# 提取结果中的 JSON 参数
tool_call = response.choices[0].message.tool_calls[0]
args = json.loads(tool_call.function.arguments)

# 打印结构化 JSON
print(json.dumps(args, indent=2, ensure_ascii=False))


