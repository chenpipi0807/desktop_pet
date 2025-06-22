"""
本地语音处理模块 - 使用Vosk离线语音识别
提供语音转文字(STT)和文字转语音(TTS)功能
"""

import json
import pyaudio
import vosk
import pyttsx3
import threading
import queue
import time
import os
import requests
import zipfile
from pathlib import Path

class LocalVoiceHandler:
    def __init__(self):
        """初始化本地语音处理器"""
        print("🎤 初始化本地语音处理器...")
        
        # 模型路径
        self.model_path = Path("vosk_model_cn")
        self.model_url = "https://alphacephei.com/vosk/models/vosk-model-cn-0.22.zip"
        
        # 音频参数 - 必须在setup_vosk_model之前定义
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 8192
        
        # 初始化Vosk模型
        self.model = None
        self.rec = None
        self.setup_vosk_model()
        
        # PyAudio
        self.audio = pyaudio.PyAudio()
        
        # TTS引擎
        self.tts_engine = pyttsx3.init()
        self.setup_tts()
        
        # 控制变量
        self.is_listening = False
        self.is_speaking = False
        self.listen_thread = None
        self.thread_lock = threading.Lock()
        
        print("✅ 本地语音处理器初始化完成")
    
    def setup_vosk_model(self):
        """设置Vosk中文模型"""
        try:
            # 检查模型是否存在
            if not self.model_path.exists():
                print("🔄 首次使用，正在下载中文语音模型...")
                self.download_chinese_model()
            
            # 加载模型
            if self.model_path.exists():
                print("📚 加载中文语音模型...")
                self.model = vosk.Model(str(self.model_path))
                self.rec = vosk.KaldiRecognizer(self.model, self.rate)
                print("✅ 中文语音模型加载成功")
            else:
                print("❌ 无法找到语音模型，请手动下载")
                
        except Exception as e:
            print(f"❌ 模型设置失败: {str(e)}")
            print("💡 请尝试手动下载模型或检查网络连接")
    
    def download_chinese_model(self):
        """下载中文语音模型"""
        try:
            model_zip = "vosk-model-cn.zip"
            
            print("⬇️ 正在下载中文语音模型（约40MB）...")
            print("🌐 下载地址：vosk官方中文模型")
            
            # 下载模型
            response = requests.get(self.model_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(model_zip, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = downloaded / total_size * 100
                        print(f"\r📥 下载进度: {percent:.1f}%", end='', flush=True)
            
            print(f"\n✅ 模型下载完成: {model_zip}")
            
            # 解压模型
            print("📦 正在解压模型...")
            with zipfile.ZipFile(model_zip, 'r') as zip_ref:
                zip_ref.extractall(".")
            
            # 重命名文件夹
            extracted_folder = None
            for item in Path(".").iterdir():
                if item.is_dir() and item.name.startswith("vosk-model-cn"):
                    extracted_folder = item
                    break
            
            if extracted_folder:
                extracted_folder.rename(self.model_path)
                print(f"✅ 模型解压完成: {self.model_path}")
            
            # 清理zip文件
            os.remove(model_zip)
            
        except Exception as e:
            print(f"❌ 模型下载失败: {str(e)}")
            print("💡 请检查网络连接或手动下载模型")
            print(f"💡 手动下载地址: {self.model_url}")
            print(f"💡 解压后重命名为: {self.model_path}")
    
    def setup_tts(self):
        """设置TTS引擎为好听的女声"""
        try:
            voices = self.tts_engine.getProperty('voices')
            
            # 寻找中文女声
            chinese_voice = None
            for voice in voices:
                if voice.id:
                    # 优先选择中文语音
                    if any(keyword in voice.id.lower() for keyword in ['zh', 'chinese', 'mandarin']):
                        chinese_voice = voice
                        break
                    # 备选：微软中文语音
                    elif any(keyword in voice.name.lower() for keyword in ['huihui', 'yaoyao', 'kangkang']):
                        chinese_voice = voice
                        break
            
            if chinese_voice:
                self.tts_engine.setProperty('voice', chinese_voice.id)
                print(f"🎤 已设置中文语音: {chinese_voice.name}")
            else:
                print("🎤 未找到中文语音，使用默认语音")
            
            # 设置语音参数
            self.tts_engine.setProperty('rate', 150)    # 语速
            self.tts_engine.setProperty('volume', 0.8)  # 音量
            
        except Exception as e:
            print(f"⚠️ TTS设置失败: {str(e)}")
    
    def listen_once(self, timeout=10):
        """单次语音识别 - 本地离线识别"""
        if not self.model or not self.rec:
            return "语音模型未加载，请检查模型文件"
        
        try:
            print("🎙️ 开始本地语音识别...")
            
            # 打开音频流
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            print("⏳ 请开始说话...")
            
            frames = []
            silent_chunks = 0
            max_silent_chunks = 30  # 大约3秒静音
            speech_detected = False
            start_time = time.time()
            
            while True:
                # 检查超时
                if time.time() - start_time > timeout:
                    print("⏱️ 录音超时")
                    break
                
                # 读取音频数据
                data = stream.read(self.chunk, exception_on_overflow=False)
                frames.append(data)
                
                # 检测语音活动
                if self.rec.AcceptWaveform(data):
                    result = json.loads(self.rec.Result())
                    if result.get('text', '').strip():
                        speech_detected = True
                        text = result['text'].strip()
                        print(f"🎯 识别到完整语句: {text}")
                        stream.stop_stream()
                        stream.close()
                        return text
                else:
                    partial = json.loads(self.rec.PartialResult())
                    if partial.get('partial', '').strip():
                        if not speech_detected:
                            speech_detected = True
                            print("🔊 检测到语音...")
                        silent_chunks = 0
                    else:
                        if speech_detected:
                            silent_chunks += 1
                            if silent_chunks >= max_silent_chunks:
                                print("🔇 检测到静音，结束录音")
                                break
            
            # 获取最终结果
            final_result = json.loads(self.rec.FinalResult())
            text = final_result.get('text', '').strip()
            
            stream.stop_stream()
            stream.close()
            
            if text:
                print(f"✅ 最终识别结果: {text}")
                return text
            else:
                return "未识别到有效语音"
                
        except Exception as e:
            print(f"❌ 语音识别失败: {str(e)}")
            return f"识别失败: {str(e)}"
    
    def speak(self, text, callback=None):
        """文字转语音播放"""
        def _speak():
            try:
                self.is_speaking = True
                print(f"🔊 本地TTS播放: {text}")
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                self.is_speaking = False
                if callback:
                    callback()
            except Exception as e:
                print(f"❌ 语音播放失败: {str(e)}")
                self.is_speaking = False
                if callback:
                    callback()
        
        thread = threading.Thread(target=_speak)
        thread.daemon = True
        thread.start()
    
    def start_continuous_listening(self, callback=None):
        """开始连续监听模式"""
        with self.thread_lock:
            if self.is_listening:
                return
            self.is_listening = True
        
        def _listen():
            while self.is_listening:
                try:
                    if not self.is_speaking:  # 只在不说话时监听
                        text = self.listen_once(timeout=5)
                        if text and not text.startswith("未识别") and not text.startswith("识别失败"):
                            if callback:
                                callback(text)
                    time.sleep(0.1)
                except Exception as e:
                    print(f"🎤 连续监听错误: {str(e)}")
                    time.sleep(1)
        
        self.listen_thread = threading.Thread(target=_listen)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        print("🎙️ 开始本地连续监听...")
    
    def stop_listening(self):
        """停止监听"""
        with self.thread_lock:
            self.is_listening = False
        print("⏹️ 停止本地监听")
    
    def is_busy(self):
        """检查是否正在处理语音"""
        return self.is_speaking or self.is_listening
    
    def stop_speaking(self):
        """停止语音播放"""
        try:
            self.tts_engine.stop()
            self.is_speaking = False
            print("⏹️ 停止语音播放")
        except Exception as e:
            print(f"停止语音播放失败: {str(e)}")
    
    def __del__(self):
        """清理资源"""
        try:
            if hasattr(self, 'audio'):
                self.audio.terminate()
        except:
            pass

# 测试代码
if __name__ == "__main__":
    voice = LocalVoiceHandler()
    
    print("测试本地语音输出...")
    voice.speak("你好！我是你的AI桌宠，现在使用本地语音识别了！")
    
    time.sleep(3)
    print("测试本地语音输入...")
    result = voice.listen_once()
    print(f"识别结果: {result}")
    
    if result and not result.startswith("未识别") and not result.startswith("识别失败"):
        voice.speak(f"你刚才说的是：{result}")
