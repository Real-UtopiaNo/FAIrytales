from openai import OpenAI
import yaml
import os
import json
from prompt import *
# from generate import *
# from t2i import *
from tts import *
from generate import generate_and_parse_story # 只导入我们需要的统一函数
from image_generator import process_story_for_images # 导入图片处理函数

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
# 1. 保持 prompt 生成逻辑不变
prompt = generate_prompt(config=config)
print("--- Generating story with the following prompt ---")
print(prompt)

# 2. 调用统一的生成和解析函数
structured_story = generate_and_parse_story(prompt=prompt)


# 3. 打印最终的结构化数据
if structured_story:
    print("\n--- Successfully generated and parsed story ---")
    print(json.dumps(structured_story, indent=2, ensure_ascii=False))

    # 直接将生成的结构化数据传递给图片处理模块
    print("\n--- Handing off to image generator ---")
    process_story_for_images(structured_story)
else:
    print("\n--- Failed to get structured story after all attempts. ---")


# os.makedirs(os.path.join("books", title), exist_ok=True)