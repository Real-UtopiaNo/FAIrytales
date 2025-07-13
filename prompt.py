def generate_prompt_example1(word_length=1000, age=5, gender="boy", moral="bravery", slides=10, **kwargs):
    characters_prompt = None
    for key, value in kwargs.items():
        if key=="characters":
            characters_prompt=f"""
            # Characters Settings
            """
            for i,character in enumerate(value):
                characters_prompt+=f"""
                {i+1}.A {character["gender"]} named {character["name"]}, whose goal in the fairytales is: {character["goal"]}
                """
                
    return f"""
    The following are settings of the fairytales:
    # General Settings
    1.Use get_fairytales function to craft an engaging fairytale that is approximately {word_length} words in length. 
    2.The story should be geared towards a {age}-year-old {gender}, with a particular theme focus on {moral}. 
    3.Use language comprehensively for a {age}-year-old child.
    {characters_prompt}
    # Part Settings
    1.The story should be broke into {slides} parts, seperate each part by "\n".
    2.Each part should be a relatively independent event or scene.
    3.Each part should be coherent and contribute to the overall narrative arc.
    4.Each part should be approximately {word_length // slides} in length.
    5.Write a short visual description (no more than 50 characters) for EACH part to be used as a prompt for text-to-image models, seperate each description by "\n".
    """

def generate_prompt_example():
    characters = [
    {"name": "John",
     "gender": "boy",
     "goal": "Defeat the dragon"
    },
    ]
    return generate_prompt_example1(characters=characters)

def generate_prompt(config):
    '''
    输入Config实例
    输出prompt字符串
    '''
    # 角色提示词
    characters_prompt = ""
    for i, character_setting in enumerate(config["characters"]):
        character_prompt = f"\t第{i+1}个角色："
        if character_setting["name"]:
            character_prompt += f"\t\t名字：{character_setting['name']}"
        if character_setting["species"]:
            character_prompt += f"\t\t物种：{character_setting['species']}"

        characters_prompt += character_prompt+"\n"

    # 文本语言
    lang = {"zh":"中文",
            "en":"英文",
            "fr":"法语",
            "ca":"粤语正字"}


    prompt = f"""
你是一名童话故事创作者。
现在请根据以下设定，生成一篇童话故事，并将其分成 {config["part_num"]} 个段落，每段约 {config["word_len"]//config["part_num"]} 字，并提供**一句**图片提示词。童话故事中必须包含指定的好词好句，以便让阅读者学习。

【设定】
标题：{config["title"]}
角色：\n{characters_prompt}
寓意：{config["lesson"]}
语言：{lang[config["language"]]}
目标年龄：{config["trg_age"]}
好词好句：{"、".join(eval(config['good_words']))}

【输出格式】
第1段：
内容：<第1段故事内容，约 {config["word_len"]//config["part_num"]} 字>
图片提示词：<用于生成图片的描述语句>

第2段：
内容：<第2段故事内容，约 {config["word_len"]//config["part_num"]} 字>
图片提示词：<用于生成图片的描述语句>

请严格遵守段落数和输出格式。
""".strip()
    return prompt

def build_prompt(config):
    avg_len = config.word_len // config.part_num
    character_names = ", ".join([c.name for c in config.characters])
    return 
