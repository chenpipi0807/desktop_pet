# 配置文件
import os

# DeepSeek API 配置
def get_api_key():
    """从key.txt文件读取API key"""
    key_file = os.path.join(os.path.dirname(__file__), 'key.txt')
    try:
        if os.path.exists(key_file):
            with open(key_file, 'r', encoding='utf-8') as f:
                key = f.read().strip()
                if key:
                    return key
        return None
    except Exception as e:
        print(f"读取API key失败: {e}")
        return None

DEEPSEEK_API_KEY = get_api_key()
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1/chat/completions"

# GUI 配置
WINDOW_WIDTH = 400
WINDOW_HEIGHT = 600
WINDOW_TITLE = "AI桌宠"
