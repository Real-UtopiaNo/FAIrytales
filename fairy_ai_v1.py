from openai import OpenAI
import yaml
import os
import json
from prompt import *
from generate import *
# from t2i import *  # t2i module not found, using image_generator instead
from tts import process_story_for_tts
from generate import generate_and_parse_story # 只导入我们需要的统一函数
from image_generator import process_story_for_images # 导入图片处理函数
from pdf_generator import process_story_for_pdf # 导入PDF生成函数
# import translators as ts

# def translate_text(text, target_language="en"):
#     # Translate using Google Translator engine
#     translated_text = ts.translate_text(text,to_language=target_language)
#     return translated_text

"""加载config文件"""
with open("config.yaml", "r", encoding='utf-8') as file:
    config = yaml.safe_load(file)


"""根据config合成prompt"""
# 1. 保持 prompt 生成逻辑不变
prompt = generate_prompt(config=config)
print("--- Generating story with the following prompt ---")
print(prompt)

"""调用LLM API获取故事内容以及文生图prompt"""
# 2. 调用统一的生成和解析函数
structured_story = generate_and_parse_story(prompt=prompt)
if structured_story:
    print("\n--- Successfully generated and parsed story ---")
    print(json.dumps(structured_story, indent=2, ensure_ascii=False))

    # 保存故事到文件
    save_success = save_story_to_files(structured_story)
    if save_success:
        print("\n--- 故事内容已成功保存到文件 ---")
    else:
        print("\n--- 保存故事内容时出错 ---")


"""生成图片和朗读音频并整合文字与图片"""
# 3. 打印最终的结构化数据
if structured_story:
    print("\n--- Successfully generated and parsed story ---")
    print(json.dumps(structured_story, indent=2, ensure_ascii=False))
    # 确保图片生成的 prompt 是英文的
    print("\n--- Ensuring all image prompts are in English ---")
    for part in structured_story.get("story_parts", []):
        # 暂时注释掉翻译功能，因为translate_text函数未定义
        # part["t2i_prompt"] = translate_text(part.get("t2i_prompt",""))
        print(f"段落 {part.get('part_number', 'N/A')} 的图片提示词: {part.get('t2i_prompt', '')}")

    # 直接将生成的结构化数据传递给图片处理模块
    print("\n--- Handing off to image generator ---")
    process_story_for_images(structured_story)
    
    # 生成TTS语音文件
    print("\n--- Handing off to TTS generator ---")
    # 可以根据配置文件中的设置来配置音色
    voice_config = {
        "default": "xiaoxiao",  # 使用测试成功的音色
        # 可以根据需要为不同段落配置不同音色
        # "part_1": "child",
        # "part_2": "mother"
    }
    
    tts_success = process_story_for_tts(structured_story, voice_config)
    if tts_success:
        print("✅ 语音文件生成完成！")
    else:
        print("❌ 语音文件生成失败")
    
    # 生成PDF文件
    print("\n--- Handing off to PDF generator ---")
    pdf_success = process_story_for_pdf(structured_story)
    if pdf_success:
        print("✅ PDF文件生成完成！")
    else:
        print("❌ PDF文件生成失败")
else:
    print("\n--- Failed to get structured story after all attempts. ---")


# os.makedirs(os.path.join("books", title), exist_ok=True)

