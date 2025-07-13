from openai import OpenAI
import yaml
import os
import json
from prompt import *
from generate import *
from t2i import *
from tts import *

"""
Create config from yaml file. Example of config:

{'title': '小熊的奇幻冒险', 'characters': [{'name': '小熊', 'trait': '勇敢'}, 
{'name': '狐狸', 'trait': '聪明'}], 'lesson': '要诚实守信', 'style': '温馨治愈', 'language': 'zh', 'voice': 'female'}
"""
with open("config.yaml", "r", encoding='utf-8') as file:
    config = yaml.safe_load(file)


"""
Get prompt for LLM, then pass it to API, return title, parts, t2iprompts, ......
"""
prompt = generate_prompt_example()
title, parts, t2iprompts = generate_content(prompt)


# os.makedirs(os.path.join("books", title), exist_ok=True)