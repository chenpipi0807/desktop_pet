"""
语音处理模块
提供语音转文字(STT)和文字转语音(TTS)功能
"""

import speech_recognition as sr
import pyttsx3
import threading
import queue
import time

class VoiceHandler:
    def __init__(self):
        """初始化语音处理器"""
        self.recognizer = sr.Recognizer()
        self.microphone = None  # 延迟初始化
        
        # 设置语音识别参数
        self.recognizer.pause_threshold = 0.8  # 0.8秒静音后认为说完一句话
        self.recognizer.phrase_threshold = 0.3  # 降低语音检测阈值，更敏感
        self.recognizer.energy_threshold = 300  # 降低能量阈值，更容易检测到语音
        self.recognizer.non_speaking_duration = 0.5  # 开始前的静音时间
        
        # TTS引擎
        self.tts_engine = pyttsx3.init()
        self.setup_tts()
        
        # 控制变量
        self.is_listening = False
        self.is_speaking = False
        self.listen_thread = None
        self.thread_lock = threading.Lock()  # 线程锁
        
        # 音频队列
        self.audio_queue = queue.Queue()
        
        # 初始化麦克风
        self.init_microphone()
    
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
                    # 备选：包含中文特征的语音
                    elif any(keyword in voice.name.lower() for keyword in ['chinese', 'zh', 'mandarin', '中文']):
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
                # 如果没有中文语音，设置语言为中文
                try:
                    self.tts_engine.setProperty('languages', 'zh')
                except:
                    pass
            
            # 设置语音参数 - 适合中文的参数
            self.tts_engine.setProperty('rate', 150)    # 降低语速，适合中文
            self.tts_engine.setProperty('volume', 0.8)  # 音量
            
        except Exception as e:
            print(f"⚠️ TTS设置失败: {str(e)}")
            # 尝试直接设置中文
            try:
                self.tts_engine.setProperty('rate', 150)
                self.tts_engine.setProperty('volume', 0.8)
            except:
                pass
    
    def init_microphone(self):
        """安全初始化麦克风"""
        try:
            self.microphone = sr.Microphone()
            print("🎙️ 正在调整麦克风...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("✅ 麦克风调整完成")
        except Exception as e:
            print(f"❌ 麦克风初始化失败: {str(e)}")
            self.microphone = None
    
    def listen_once(self, timeout=10):
        """单次语音识别 - 智能监听模式：检测到语音后，等待0.8秒静音才结束"""
        try:
            print("🎙️ 开始监听...")
            with self.microphone as source:
                # 等待检测到语音输入并录音
                print("⏳ 等待您开始说话...")
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout,           # 等待开始说话的超时时间
                    phrase_time_limit=None     # 不限制单次录音长度，由pause_threshold控制
                )
            
            print("🔄 正在识别语音...")
            # 使用Google语音识别（中文），添加更多语言选项提高准确度
            try:
                # 首先尝试中文识别
                text = self.recognizer.recognize_google(audio, language='zh-CN')
            except sr.UnknownValueError:
                # 如果中文识别失败，尝试中文（台湾）
                try:
                    text = self.recognizer.recognize_google(audio, language='zh-TW')
                except sr.UnknownValueError:
                    # 最后尝试中文（香港）
                    text = self.recognizer.recognize_google(audio, language='zh-HK')
            
            print(f"✅ 识别结果: {text}")
            return text
            
        except sr.WaitTimeoutError:
            return "超时：没有检测到语音"
        except sr.UnknownValueError:
            return "抱歉，我没有听清楚您说的话"
        except sr.RequestError as e:
            return f"语音识别服务出错: {str(e)}"
        except Exception as e:
            return f"语音识别失败: {str(e)}"
    
    def speak(self, text, callback=None):
        """文字转语音播放"""
        def _speak():
            try:
                self.is_speaking = True
                print(f"🔊 正在播放: {text}")
                
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                
                self.is_speaking = False
                print("✅ 语音播放完成")
                
                if callback:
                    callback()
                    
            except Exception as e:
                self.is_speaking = False
                print(f"⚠️ 语音播放失败: {str(e)}")
                if callback:
                    callback()
        
        # 在单独线程中播放语音
        speak_thread = threading.Thread(target=_speak)
        speak_thread.daemon = True
        speak_thread.start()
    
    def stop_listening(self):
        """安全停止监听"""
        with self.thread_lock:
            if self.is_listening:
                self.is_listening = False
                print("⏹️ 停止监听")
                
                # 等待监听线程结束
                if self.listen_thread and self.listen_thread.is_alive():
                    self.listen_thread.join(timeout=2)
                
                # 重新初始化麦克风，清除可能的状态问题
                self.init_microphone()

    def start_continuous_listening(self, callback=None):
        """开始连续监听模式 - 每次创建新麦克风对象"""
        with self.thread_lock:
            if self.is_listening:
                return
            self.is_listening = True
        
        def _listen():
            consecutive_errors = 0
            max_errors = 5
            
            while self.is_listening:
                try:
                    # 每次监听都创建全新的麦克风对象 - 避免上下文冲突
                    mic = sr.Microphone()
                    
                    with mic as source:
                        # 快速调整环境噪音
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                        
                        # 监听语音
                        audio = self.recognizer.listen(
                            source, 
                            timeout=2,
                            phrase_time_limit=None
                        )
                    
                    # 在with语句外进行语音识别
                    text = None
                    try:
                        text = self.recognizer.recognize_google(audio, language='zh-CN')
                        consecutive_errors = 0  # 重置错误计数
                    except sr.UnknownValueError:
                        try:
                            text = self.recognizer.recognize_google(audio, language='zh-TW')
                            consecutive_errors = 0
                        except sr.UnknownValueError:
                            try:
                                text = self.recognizer.recognize_google(audio, language='zh-HK')
                                consecutive_errors = 0
                            except sr.UnknownValueError:
                                pass
                    
                    if text and callback:
                        callback(text)
                    
                    time.sleep(0.1)
                    
                except sr.WaitTimeoutError:
                    # 正常超时，继续监听
                    pass
                except Exception as e:
                    consecutive_errors += 1
                    error_msg = f"语音识别失败: {str(e)}"
                    print(f"🎤 {error_msg}")
                    
                    if callback:
                        callback(error_msg)
                    
                    # 连续错误过多时稍微等待更久
                    if consecutive_errors >= max_errors:
                        print("❌ 连续错误过多，暂停1秒...")
                        time.sleep(1)
                        consecutive_errors = 0
                    else:
                        time.sleep(0.5)
        
        self.listen_thread = threading.Thread(target=_listen)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        print("🎙️ 开始连续监听...")
    
    def listen(self, timeout=5):
        """语音识别（兼容性方法）"""
        return self.listen_once(timeout)
    
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

# 测试代码
if __name__ == "__main__":
    voice = VoiceHandler()
    
    print("测试语音输出...")
    voice.speak("你好！我是你的AI桌宠，请对我说话吧！")
    
    time.sleep(3)
    print("测试语音输入...")
    result = voice.listen_once()
    print(f"识别结果: {result}")
    
    if result and not result.startswith("超时") and not result.startswith("抱歉"):
        voice.speak(f"你刚才说的是：{result}")
