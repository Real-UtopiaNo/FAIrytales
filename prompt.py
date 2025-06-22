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

def generate_prompt(config_file):
    '''
    输入config.json文件的路径
    输出prompt字符串
    '''
    pass