from openai import OpenAI
import os
import json
from prompt import *
from generate import *
from t2i import *
from tts import *



prompt = generate_prompt_example()
title, parts, t2iprompts = generate_content(prompt)


# os.makedirs(os.path.join("books", title), exist_ok=True)