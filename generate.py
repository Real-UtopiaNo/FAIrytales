import re
import json
from openai import OpenAI

# Initialize OpenAI client, compatible with DeepSeek API
client = OpenAI(
    api_key="sk-38195cc9744a44e385c221cb7b865ecc",  # Replace with your DeepSeek API key
    base_url="https://api.deepseek.com/v1"
)

# --- Method 1: Function Calling (Preferred) ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "create_fairytale",
            "description": "Creates a multi-part fairytale story with a title, and for each part, provides content and a visual description for an image.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title of the fairytale, based on the user's prompt."
                    },
                    "story_parts": {
                        "type": "array",
                        "description": "An array of story parts, each with its content and an image prompt.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "part_number": {"type": "integer", "description": "The sequence number of this part."},
                                "content": {"type": "string", "description": "The text content for this part."},
                                "t2i_prompt": {"type": "string", "description": "A prompt for generating an illustration for this part."},
                                "width": {"type": "integer", "description": "Appropriate Width for the image,each part can be different."},
                                "height": {"type": "integer", "description": "Appropriate Height for the image,,each part can be different."}
                            },
                            "required": ["part_number", "content", "t2i_prompt", "width", "height"]
                        }
                    }
                },
                "required": ["title", "story_parts"]
            }
        }
    }
]

# --- Method 2: Regex Parsing (Fallback) ---
def parse_story_with_regex(text_blob: str, default_width: int = 512, default_height: int = 512):
    """
    Use regex to parse structured story data from raw text returned by LLM.
    """
    print("--- Attempting to parse with Regex ---")
    pattern = re.compile(r"第(\d+)段：\s*内容：(.*?)\s*图片提示词：(.*?)(?=\s*第\d+段：|$)", re.DOTALL)
    matches = pattern.findall(text_blob)
    
    story_parts = []
    if not matches:
        print("Warning: Regex did not find any matches.")
        return None

    for match in matches:
        part_number, content, image_prompt = match
        story_parts.append({
            "part_number": int(part_number.strip()),
            "content": content.strip(),
            "t2i_prompt": image_prompt.strip(),
            "width": default_width,  # Set the default width
            "height": default_height  # Set the default height
        })
    
    # Attempt to extract the title from the first line of text
    title_match = re.search(r"标题：(.*?)\n", text_blob)
    title = title_match.group(1).strip() if title_match else "Story Title (Parsed by Regex)"
    
    return {"title": title, "story_parts": story_parts}

# --- Unified Generation and Parsing Function ---
def generate_and_parse_story(prompt: str, default_width: int = 512, default_height: int = 512):
    """
    First try Function Calling, if it fails, fall back to Regex parsing.
    """
    print("--- Calling LLM with Function Calling enabled ---")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[ 
            {"role": "system", "content": "You are a helpful fairytale author. Prioritize using the `create_fairytale` function. If you cannot, fall back to providing a raw text response in the requested format."},
            {"role": "user", "content": prompt}
        ],
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message
    
    # Prioritize Function Calling
    if message.tool_calls:
        print("--- Success: LLM used Function Calling! ---")
        tool_call = message.tool_calls[0]
        if tool_call.function.name == 'create_fairytale':
            story_data = json.loads(tool_call.function.arguments)
            # Add width and height to story parts if they are missing
            for part in story_data.get("story_parts", []):
                part["width"] = part.get("width", default_width)
                part["height"] = part.get("height", default_height)
            return story_data
    
    # If Function Calling is not used, try Regex parsing
    print("--- Fallback: LLM did not use Function Calling. ---")
    raw_text = message.content
    if raw_text:
        return parse_story_with_regex(raw_text, default_width, default_height)
        
    # If both methods fail
    print("--- Error: Both Function Calling and Regex parsing failed. ---")
    return None

# Example usage
if __name__ == "__main__":
    prompt = "Please generate a fairytale story about a boy and a bird with image prompts for each part."
    
    # Generate and parse the story with width and height for each part
    structured_story = generate_and_parse_story(prompt)

    if structured_story:
        print("\n--- Successfully generated and parsed story ---")
        print(json.dumps(structured_story, indent=2, ensure_ascii=False))

        # Optionally, print the parts and verify width and height
        for part in structured_story.get("story_parts", []):
            print(f"Part {part['part_number']} - Width: {part['width']}, Height: {part['height']}")
    else:
        print("--- Failed to generate and parse the story ---")
