"""
安装Edge-TTS依赖包
运行此脚本来安装更好的语音引擎
"""

import subprocess
import sys

def install_packages():
    """安装所需的包"""
    packages = [
        "edge-tts",     # Edge TTS引擎
        "pygame"        # 音频播放
    ]
    
    print("🔄 正在安装Edge-TTS依赖包...")
    
    for package in packages:
        print(f"安装 {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} 安装成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ {package} 安装失败: {e}")
            return False
    
    print("🎉 所有依赖包安装完成！")
    return True

if __name__ == "__main__":
    success = install_packages()
    if success:
        print("\n🎵 现在可以使用高质量的Edge-TTS语音了！")
        print("请重新启动桌宠程序来体验更好的语音效果。")
    else:
        print("\n⚠️ 安装过程中出现错误，请检查网络连接或手动安装。")
    
    input("按回车键退出...")
