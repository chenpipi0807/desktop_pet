"""
AI动画制作工具 v3.0 - 批量处理版
支持批量将多个视频转换为透明背景GIF动画
"""

import cv2
import numpy as np
from PIL import Image, ImageTk, ImageSequence
import os
from rembg import remove
import glob

class VideoProcessor:
    def __init__(self, source_dir="image", output_dir="image"):
        self.source_dir = source_dir
        self.output_dir = output_dir
        
        # 动画类别配置
        self.animation_config = {
            "basic": ["基础01", "基础02", "基础03", "基础04", "基础05"],
            "emotions": {
                "sad": "伤心",
                "surprised": "吃惊", 
                "shy": "害羞",
                "angry": "愤怒",
                "praise": "称赞",
                "contempt": "鄙视"
            }
        }
        
        print("🐼 AI动画制作工具 v3.0 - 批量处理版")
        print("=" * 60)
        self.check_dependencies()
    
    def check_dependencies(self):
        """检查依赖包"""
        try:
            import cv2
            import numpy as np
            from PIL import Image
            from rembg import remove
            print("✅ 所有依赖包检查通过")
        except ImportError as e:
            print(f"❌ 缺少依赖包: {e}")
            exit(1)
    
    def get_video_files(self):
        """获取所有需要处理的视频文件"""
        video_files = []
        pattern = os.path.join(self.source_dir, "*.mp4")
        
        for file_path in glob.glob(pattern):
            filename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(filename)[0]
            
            # 检查是否已经存在对应的GIF
            gif_path = os.path.join(self.output_dir, f"{name_without_ext}.gif")
            if not os.path.exists(gif_path):
                video_files.append((file_path, name_without_ext))
            else:
                print(f"⏭️ 跳过已存在的GIF: {name_without_ext}.gif")
        
        return video_files
    
    def extract_frames(self, video_path, max_frames=None):
        """提取视频帧"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise Exception(f"无法打开视频文件: {video_path}")
        
        # 获取视频信息
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"视频信息: {total_frames} 帧, {fps:.2f} FPS")
        
        # 计算抽帧间隔
        if max_frames is None or total_frames <= max_frames:
            frame_step = 1
            target_frames = total_frames
            print(f"📽️ 将提取全部 {total_frames} 帧")
        else:
            frame_step = total_frames // max_frames
            target_frames = max_frames
            print(f"📽️ 将从 {total_frames} 帧中抽取 {target_frames} 帧 (每 {frame_step} 帧抽一帧)")
        
        frames = []
        frame_count = 0
        
        while cap.isOpened() and len(frames) < target_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_step == 0:
                frames.append(frame)
            
            frame_count += 1
        
        cap.release()
        print(f"✅ 提取了 {len(frames)} 帧")
        return frames
    
    def remove_watermark(self, frame):
        """移除右下角水印"""
        height, width = frame.shape[:2]
        
        # 定义水印区域 (右下角)
        watermark_region = frame[int(height*0.8):height, int(width*0.7):width]
        
        # 创建掩码
        mask = np.zeros(watermark_region.shape[:2], dtype=np.uint8)
        mask.fill(255)
        
        # 使用inpaint移除水印
        result_region = cv2.inpaint(watermark_region, mask, 3, cv2.INPAINT_TELEA)
        
        # 将结果放回原图
        result_frame = frame.copy()
        result_frame[int(height*0.8):height, int(width*0.7):width] = result_region
        
        return result_frame
    
    def remove_background(self, frame):
        """移除背景，保持透明"""
        # 转换为PIL格式
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)
        
        # 移除背景
        result = remove(pil_image)
        
        return result
    
    def process_single_video(self, video_path, output_name):
        """处理单个视频"""
        print(f"\n🎬 处理视频: {output_name}")
        print("-" * 40)
        
        try:
            # 提取帧
            print("📹 正在提取视频帧...")
            frames = self.extract_frames(video_path)
            
            processed_frames = []
            total_frames = len(frames)
            
            for i, frame in enumerate(frames):
                print(f"📸 处理第 {i+1}/{total_frames} 帧...")
                
                # 移除水印
                print("🧹 正在移除水印...")
                frame_no_watermark = self.remove_watermark(frame)
                
                # 移除背景
                print("🎨 正在移除背景...")
                transparent_frame = self.remove_background(frame_no_watermark)
                
                # 调整大小
                resized_frame = transparent_frame.resize((150, 150), Image.Resampling.LANCZOS)
                processed_frames.append(resized_frame)
            
            # 创建GIF
            print("🎬 正在创建GIF动画...")
            output_path = os.path.join(self.output_dir, f"{output_name}.gif")
            
            processed_frames[0].save(
                output_path,
                save_all=True,
                append_images=processed_frames[1:],
                duration=42,  # 24fps (1000ms ÷ 24 ≈ 42ms) - 保持5秒播放时间
                loop=0,
                transparency=0,
                disposal=2
            )
            
            # 获取文件大小
            file_size = os.path.getsize(output_path) / 1024  # KB
            
            print(f"✅ GIF动画已保存: {output_name}.gif")
            print(f"📏 文件大小: {file_size:.1f} KB")
            print(f"🖼️ 帧数: {len(processed_frames)}")
            
            return True
            
        except Exception as e:
            print(f"❌ 处理失败: {str(e)}")
            return False
    
    def process_all_videos(self):
        """批量处理所有视频"""
        video_files = self.get_video_files()
        
        if not video_files:
            print("🎉 所有视频都已转换完成！")
            return
        
        print(f"🚀 开始批量处理 {len(video_files)} 个视频文件...")
        print("=" * 60)
        
        success_count = 0
        total_count = len(video_files)
        
        for video_path, output_name in video_files:
            if self.process_single_video(video_path, output_name):
                success_count += 1
        
        print("\n" + "=" * 60)
        print(f"🎊 批量处理完成！")
        print(f"📊 成功: {success_count}/{total_count}")
        
        if success_count == total_count:
            print("🎉 所有视频转换成功！")
            self.show_animation_summary()
        else:
            print(f"⚠️ {total_count - success_count} 个视频处理失败")
    
    def show_animation_summary(self):
        """显示动画库总结"""
        print("\n🎭 动画库总结:")
        print("-" * 40)
        
        # 基础动画
        print("📂 基础动画 (随机播放):")
        for basic_name in self.animation_config["basic"]:
            gif_path = os.path.join(self.output_dir, f"{basic_name}.gif")
            if os.path.exists(gif_path):
                print(f"  ✅ {basic_name}.gif")
            else:
                print(f"  ❌ {basic_name}.gif (缺失)")
        
        # 情绪动画
        print("\n😊 情绪动画 (AI触发):")
        for emotion_key, emotion_name in self.animation_config["emotions"].items():
            gif_path = os.path.join(self.output_dir, f"{emotion_name}.gif")
            if os.path.exists(gif_path):
                print(f"  ✅ {emotion_name}.gif ({emotion_key})")
            else:
                print(f"  ❌ {emotion_name}.gif ({emotion_key}) (缺失)")
        
        print(f"\n🎯 下一步: 运行 voice_pet.py 查看多动画效果！")

# 主程序
if __name__ == "__main__":
    try:
        processor = VideoProcessor()
        processor.process_all_videos()
        
        print("\n按回车键退出...")
        input()
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户取消操作")
    except Exception as e:
        print(f"\n❌ 程序异常: {str(e)}")
        print("\n按回车键退出...")
        input()
