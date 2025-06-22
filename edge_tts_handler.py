"""
Edge-TTS语音处理模块
使用微软Edge的高质量TTS引擎
"""

import asyncio
import edge_tts
import pygame
import io
import threading
import tempfile
import os

class EdgeTTSHandler:
    def __init__(self):
        # 初始化pygame音频
        pygame.mixer.init()
        
        # 中文语音选项（可以根据喜好调整）
        self.voice_options = {
            "温柔女声": "zh-CN-XiaoxiaoNeural",      # 温柔甜美
            "活泼女声": "zh-CN-XiaoyiNeural",        # 活泼可爱  
            "成熟女声": "zh-CN-XiaohanNeural",       # 成熟稳重
            "萌妹女声": "zh-CN-XiaomengNeural",      # 萌萌哒
            "清纯女声": "zh-CN-XiaomoNeural",       # 清纯甜美
            "温暖男声": "zh-CN-YunxiNeural",        # 温暖男声
            "新闻男声": "zh-CN-YunyangNeural",      # 新闻主播风格
            "少年音": "zh-CN-YunjianNeural"          # 少年音
        }
        
        # 默认使用活泼女声
        self.current_voice_name = "活泼女声"
        self.current_voice = self.voice_options[self.current_voice_name]
        
        self.is_speaking = False
        
    async def _generate_speech(self, text):
        """异步生成语音"""
        try:
            # 清理文本，移除可能导致问题的字符
            text = text.strip()
            if not text:
                return None
            
            # 替换可能导致问题的特殊字符
            text = text.replace('(', '，').replace(')', '').replace('[', '').replace(']', '')
            
            communicate = edge_tts.Communicate(text, self.current_voice)
            
            # 生成音频数据，增加超时控制
            audio_data = b""
            chunk_count = 0
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
                    chunk_count += 1
                    if chunk_count > 1000:  # 防止无限循环
                        break
            
            if len(audio_data) < 1000:  # 音频数据太小，可能有问题
                print(f"⚠️ 音频数据异常小: {len(audio_data)} 字节")
                return None
                
            return audio_data
        except Exception as e:
            print(f"生成语音失败: {str(e)}")
            return None
    
    def speak(self, text, callback=None):
        """文字转语音播放"""
        if not text or not text.strip():
            return
            
        def speak_thread():
            try:
                self.is_speaking = True
                print(f"🔊 Edge-TTS正在播放: {text}")
                
                # 在新的事件循环中运行异步函数
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                audio_data = loop.run_until_complete(self._generate_speech(text))
                loop.close()
                
                if audio_data:
                    # 创建临时文件播放音频
                    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                        temp_file.write(audio_data)
                        temp_file_path = temp_file.name
                    
                    try:
                        # 使用pygame播放音频
                        pygame.mixer.music.load(temp_file_path)
                        pygame.mixer.music.play()
                        
                        # 等待播放完成
                        while pygame.mixer.music.get_busy():
                            pygame.time.wait(100)
                        
                        print("✅ Edge-TTS播放完成")
                    finally:
                        # 清理临时文件
                        try:
                            os.unlink(temp_file_path)
                        except:
                            pass
                else:
                    print("❌ Edge-TTS生成失败")
                    
            except Exception as e:
                print(f"⚠️ Edge-TTS播放失败: {str(e)}")
            finally:
                self.is_speaking = False
                if callback:
                    callback()
        
        # 在单独线程中播放语音
        thread = threading.Thread(target=speak_thread)
        thread.daemon = True
        thread.start()
    
    def stop_speaking(self):
        """停止语音播放"""
        try:
            pygame.mixer.music.stop()
            self.is_speaking = False
            print("⏹️ 停止Edge-TTS播放")
        except Exception as e:
            print(f"停止语音播放失败: {str(e)}")
    
    def set_voice(self, voice_name):
        """设置语音"""
        if voice_name in self.voice_options:
            self.current_voice_name = voice_name
            self.current_voice = self.voice_options[self.current_voice_name]
            print(f"🎤 已切换到语音: {voice_name}")
        else:
            print(f"⚠️ 未知语音: {voice_name}")
    
    def list_voices(self):
        """列出可用语音"""
        return list(self.voice_options.keys())

# 测试代码
if __name__ == "__main__":
    tts = EdgeTTSHandler()
    print("测试Edge-TTS...")
    tts.speak("你好！我是使用Edge TTS的高质量语音助手！")
    
    import time
    time.sleep(5)  # 等待播放完成
