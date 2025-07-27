import asyncio
import edge_tts
import os
import json
from typing import Dict, List, Optional

class TTSGenerator:
    """
    文本转语音生成器，使用edge-tts库实现
    支持多种中文音色和自定义音色选择
    """
    
    # 预定义的中文音色选项
    CHINESE_VOICES = {
        "xiaoxiao": "zh-CN-XiaoxiaoNeural",      # 女声，温柔
        "yunxi": "zh-CN-YunxiNeural",            # 男声，温和
        "xiaoyi": "zh-CN-XiaoyiNeural",          # 女声，甜美
        "yunjian": "zh-CN-YunjianNeural",        # 男声，成熟
        "xiaomo": "zh-CN-XiaomoNeural",          # 女声，亲切
        "yunyang": "zh-CN-YunyangNeural",        # 男声，阳光
        "xiaohan": "zh-CN-XiaohanNeural",        # 女声，知性
        "yunhao": "zh-CN-YunhaoNeural",          # 男声，稳重
    }
    
    # 英文音色选项
    ENGLISH_VOICES = {
        "aria": "en-US-AriaNeural",              # 女声，自然
        "guy": "en-US-GuyNeural",                # 男声，友好
        "jenny": "en-US-JennyNeural",            # 女声，温暖
        "davis": "en-US-DavisNeural",            # 男声，专业
        "jane": "en-US-JaneNeural",              # 女声，清晰
        "jason": "en-US-JasonNeural",            # 男声，稳重
        "sara": "en-US-SaraNeural",              # 女声，友善
        "tony": "en-US-TonyNeural",              # 男声，活力
    }
    
    # 角色音色映射（父母、朋友等）
    CHARACTER_VOICES = {
        # 中文角色音色
        "father": "zh-CN-YunjianNeural",         # 父亲音色
        "mother": "zh-CN-XiaoxiaoNeural",        # 母亲音色
        "friend": "zh-CN-XiaoyiNeural",          # 朋友音色
        "narrator": "zh-CN-XiaoxiaoNeural",      # 旁白音色
        "child": "zh-CN-XiaoyiNeural",           # 儿童音色
        
        # 英文角色音色
        "father_en": "en-US-GuyNeural",          # 英文父亲音色
        "mother_en": "en-US-AriaNeural",         # 英文母亲音色
        "friend_en": "en-US-JennyNeural",        # 英文朋友音色
        "narrator_en": "en-US-DavisNeural",      # 英文旁白音色
        "child_en": "en-US-JaneNeural",          # 英文儿童音色
    }
    
    def __init__(self, default_voice: str = "xiaoxiao"):
        """
        初始化TTS生成器
        
        Args:
            default_voice: 默认音色名称
        """
        self.default_voice = self._get_voice_id(default_voice)
        
    def _get_voice_id(self, voice_name: str) -> str:
        """
        获取音色ID
        
        Args:
            voice_name: 音色名称
            
        Returns:
            音色ID字符串
        """
        # 首先检查是否是预定义的中文音色
        if voice_name in self.CHINESE_VOICES:
            return self.CHINESE_VOICES[voice_name]
        
        # 检查是否是预定义的英文音色
        if voice_name in self.ENGLISH_VOICES:
            return self.ENGLISH_VOICES[voice_name]
        
        # 检查是否是角色音色
        if voice_name in self.CHARACTER_VOICES:
            return self.CHARACTER_VOICES[voice_name]
        
        # 如果是完整的音色ID，直接返回
        if voice_name.startswith("zh-CN-") or voice_name.startswith("en-US-"):
            return voice_name
            
        # 默认返回xiaoxiao音色
        return self.CHINESE_VOICES["xiaoxiao"]
    
    async def text_to_speech_async(self, text: str, output_path: str, voice: Optional[str] = None, max_retries: int = 3) -> bool:
        """
        异步文本转语音
        
        Args:
            text: 要转换的文本
            output_path: 输出音频文件路径
            voice: 音色名称，如果为None则使用默认音色
            max_retries: 最大重试次数
            
        Returns:
            转换是否成功
        """
        # 检查文本是否为空
        if not text or not text.strip():
            print(f"警告：文本内容为空，跳过语音生成")
            return False
        
        # 确定使用的音色
        voice_id = self._get_voice_id(voice) if voice else self.default_voice
        
        # 创建输出目录（如果路径包含目录）
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # 处理过长的文本（edge-tts有字符限制）
        max_length = 1000  # 减少最大字符数以提高稳定性
        if len(text) > max_length:
            print(f"警告：文本长度({len(text)})超过限制({max_length})，将截断处理")
            text = text[:max_length]
        
        print(f"🔊 正在生成语音: {output_path}")
        print(f"   使用音色: {voice_id}")
        print(f"   文本长度: {len(text)} 字符")
        print(f"   文本内容: {text[:50]}{'...' if len(text) > 50 else ''}")
        
        # 重试机制
        for attempt in range(max_retries):
            try:
                print(f"   尝试 {attempt + 1}/{max_retries}")
                
                # 创建TTS通信对象
                communicate = edge_tts.Communicate(text, voice_id)
                
                # 生成语音并保存
                await communicate.save(output_path)
                
                # 检查文件是否成功生成
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    print(f"✅ 成功生成语音文件：{output_path}")
                    return True
                else:
                    print(f"⚠️  文件生成但为空，尝试重新生成...")
                    continue
                    
            except Exception as e:
                print(f"❌ 第{attempt + 1}次尝试失败：{e}")
                if attempt < max_retries - 1:
                    print(f"   等待2秒后重试...")
                    await asyncio.sleep(2)
                else:
                    print(f"❌ 所有重试都失败了")
        
        return False
    
    def text_to_speech(self, text: str, output_path: str, voice: Optional[str] = None) -> bool:
        """
        同步文本转语音接口
        
        Args:
            text: 要转换的文本
            output_path: 输出音频文件路径
            voice: 音色名称，如果为None则使用默认音色
            
        Returns:
            转换是否成功
        """
        return asyncio.run(self.text_to_speech_async(text, output_path, voice))
    
    async def generate_story_audio_async(self, story_data: Dict, base_path: str = "books", voice_config: Optional[Dict] = None) -> bool:
        """
        异步为整个故事生成语音文件
        
        Args:
            story_data: 故事数据字典
            base_path: 基础路径
            voice_config: 音色配置字典，可以为不同部分指定不同音色
            
        Returns:
            生成是否成功
        """
        try:
            title = story_data.get("title", "未命名故事")
            story_parts = story_data.get("story_parts", [])
            
            # 创建故事文件夹
            story_folder = os.path.join(base_path, title)
            os.makedirs(story_folder, exist_ok=True)
            
            # 为每个段落生成语音
            for part in story_parts:
                part_number = part.get("part_number", 1)
                content = part.get("content", "")
                
                if not content.strip():
                    print(f"警告：第{part_number}段内容为空，跳过语音生成")
                    continue
                
                # 确定使用的音色
                voice = None
                if voice_config:
                    voice = voice_config.get(f"part_{part_number}", voice_config.get("default"))
                
                # 生成音频文件路径
                audio_filename = f"voice{part_number}.wav"
                audio_path = os.path.join(story_folder, audio_filename)
                
                # 生成语音
                success = await self.text_to_speech_async(content, audio_path, voice)
                if not success:
                    print(f"第{part_number}段语音生成失败")
                    return False
                    
            print(f"故事《{title}》的所有语音文件生成完成")
            return True
            
        except Exception as e:
            print(f"生成故事语音时出错：{e}")
            return False
    
    def generate_story_audio(self, story_data: Dict, base_path: str = "books", voice_config: Optional[Dict] = None) -> bool:
        """
        同步为整个故事生成语音文件
        
        Args:
            story_data: 故事数据字典
            base_path: 基础路径
            voice_config: 音色配置字典
            
        Returns:
            生成是否成功
        """
        return asyncio.run(self.generate_story_audio_async(story_data, base_path, voice_config))
    
    def get_available_voices(self) -> Dict[str, str]:
        """
        获取可用的音色列表
        
        Returns:
            音色名称到音色ID的映射字典
        """
        all_voices = {}
        all_voices.update(self.CHINESE_VOICES)
        all_voices.update(self.ENGLISH_VOICES)
        all_voices.update(self.CHARACTER_VOICES)
        return all_voices
    
    async def get_edge_voices_async(self) -> List[Dict]:
        """
        异步获取所有可用的edge-tts音色
        
        Returns:
            音色信息列表
        """
        try:
            voices = await edge_tts.list_voices()
            # 过滤出中文音色
            chinese_voices = [voice for voice in voices if voice['Locale'].startswith('zh-')]
            return chinese_voices
        except Exception as e:
            print(f"获取音色列表时出错：{e}")
            return []
    
    def get_edge_voices(self) -> List[Dict]:
        """
        同步获取所有可用的edge-tts音色
        
        Returns:
            音色信息列表
        """
        return asyncio.run(self.get_edge_voices_async())


def process_story_for_tts(story_data: Dict, voice_config: Optional[Dict] = None) -> bool:
    """
    处理故事数据并生成TTS音频文件
    这是主要的对外接口函数
    
    Args:
        story_data: 故事数据字典
        voice_config: 音色配置字典，例如：
                     {
                         "default": "xiaoxiao",
                         "part_1": "father",
                         "part_2": "mother"
                     }
    
    Returns:
        处理是否成功
    """
    try:
        # 创建TTS生成器
        tts_generator = TTSGenerator()
        
        # 生成语音文件
        success = tts_generator.generate_story_audio(story_data, voice_config=voice_config)
        
        if success:
            print("✅ TTS处理完成！所有语音文件已生成")
        else:
            print("❌ TTS处理失败")
            
        return success
        
    except Exception as e:
        print(f"TTS处理过程中出错：{e}")
        return False


# 示例使用代码
if __name__ == "__main__":
    # 创建TTS生成器
    tts = TTSGenerator()
    
    # 显示可用音色
    print("可用音色：")
    voices = tts.get_available_voices()
    for name, voice_id in voices.items():
        print(f"  {name}: {voice_id}")
    
    # 测试单个文本转语音
    test_text = "从前有一个小男孩，他非常喜欢听故事。"
    test_output = "test_voice.wav"
    
    print(f"\n测试文本转语音...")
    success = tts.text_to_speech(test_text, test_output, "xiaoxiao")
    if success:
        print(f"测试成功！音频文件已保存到：{test_output}")
    else:
        print("测试失败！")
    
    # 测试故事数据处理
    sample_story = {
        "title": "测试故事",
        "story_parts": [
            {
                "part_number": 1,
                "content": "从前有一个勇敢的小男孩。",
                "t2i_prompt": "A brave little boy",
                "width": 512,
                "height": 512
            },
            {
                "part_number": 2,
                "content": "他遇到了一只会说话的小鸟。",
                "t2i_prompt": "A talking bird",
                "width": 512,
                "height": 512
            }
        ]
    }
    
    # 配置不同段落使用不同音色
    voice_config = {
        "default": "narrator",
        "part_1": "child",
        "part_2": "friend"
    }
    
    print(f"\n测试故事语音生成...")
    success = process_story_for_tts(sample_story, voice_config)
    if success:
        print("故事语音生成测试成功！")
    else:
        print("故事语音生成测试失败！")
