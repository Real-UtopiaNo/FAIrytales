import yaml
import os
import json
from openai import OpenAI


# --- 全局配置和客户端 ---
_config = None
_provider = None
_clients = {}
_models = {}

def load_config(config_path="config.yaml"):
    """加载并解析LLM的配置"""
    global _config, _provider, _models, _clients
    # 重置状态以允许重新加载（例如，切换provider后）
    _config = None
    _clients = {}
    
    with open(config_path, "r", encoding='utf-8') as file:
        _config = yaml.safe_load(file)["llm"]
    _provider = _config["provider"]
    
    # 存储模型名称
    provider_config = _config[_provider]
    _models['generation'] = provider_config['generation_model']
    _models['safety_check'] = provider_config['safety_check_model']
    return _config

def _get_client():
    """根据配置初始化并返回对应的API客户端 (单例模式)"""
    global _clients
    if _provider not in _clients:
        provider_config = _config[_provider]
        _clients[_provider] = OpenAI(
            api_key=provider_config["api_key"],
            base_url=provider_config["base_url"]
        )
    return _clients[_provider]

# --- 统一的API调用接口 ---
def generate_content(messages: list, is_json: bool = False, model_type: str = 'generation') -> str:
    """
    使用配置的LLM provider生成内容。
    适用于DeepSeek和Qwen等OpenAI兼容API。
    """
    client = _get_client()
    model_name = _models[model_type]

    response_format = {"type": "json_object"} if is_json else {"type": "text"}
    
    completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        response_format=response_format
    )
    return completion.choices[0].message.content

def generate_content_with_tools(messages: list, tools: list, model_type: str = 'generation') -> dict:
    """
    专用于支持Function Calling的OpenAI兼容API（如DeepSeek, Qwen）。
    """
    client = _get_client()
    model_name = _models[model_type]
    
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    return response.choices[0].message
