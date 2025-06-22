import tkinter as tk
from PIL import Image, ImageTk
import io
import base64
from PIL import ImageGrab
import os
from datetime import datetime

class ScreenCapture:
    def __init__(self):
        self.screenshot_dir = "screenshots"
        self.ensure_screenshot_dir()
    
    def ensure_screenshot_dir(self):
        """确保截图目录存在"""
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
    
    def capture_full_screen(self, save_to_file=False):
        """
        截取全屏
        
        Args:
            save_to_file (bool): 是否保存到文件
            
        Returns:
            PIL.Image: 截图图像对象
        """
        try:
            # 使用PIL的ImageGrab截取全屏
            screenshot = ImageGrab.grab()
            
            if save_to_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                filepath = os.path.join(self.screenshot_dir, filename)
                screenshot.save(filepath)
                print(f"截图已保存到: {filepath}")
            
            return screenshot
            
        except Exception as e:
            print(f"截图失败: {str(e)}")
            return None
    
    def capture_region(self, bbox, save_to_file=False):
        """
        截取指定区域
        
        Args:
            bbox (tuple): (left, top, right, bottom) 区域坐标
            save_to_file (bool): 是否保存到文件
            
        Returns:
            PIL.Image: 截图图像对象
        """
        try:
            # 截取指定区域
            screenshot = ImageGrab.grab(bbox=bbox)
            
            if save_to_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"region_{timestamp}.png"
                filepath = os.path.join(self.screenshot_dir, filename)
                screenshot.save(filepath)
                print(f"区域截图已保存到: {filepath}")
            
            return screenshot
            
        except Exception as e:
            print(f"区域截图失败: {str(e)}")
            return None
    
    def image_to_base64(self, image):
        """
        将PIL图像转换为base64编码字符串
        
        Args:
            image (PIL.Image): 图像对象
            
        Returns:
            str: base64编码的图像字符串
        """
        try:
            # 将图像保存到内存中的字节流
            buffer = io.BytesIO()
            
            # 压缩图像以减少API调用的数据量
            # 如果图像太大，先调整大小
            max_size = 1024  # 最大边长
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
            
            # 保存为JPEG格式以减少大小
            if image.mode == 'RGBA':
                # 如果是RGBA模式，先转换为RGB
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = rgb_image
            
            image.save(buffer, format='JPEG', quality=85)
            
            # 获取字节数据并转换为base64
            image_data = buffer.getvalue()
            base64_string = base64.b64encode(image_data).decode('utf-8')
            
            return base64_string
            
        except Exception as e:
            print(f"图像转换base64失败: {str(e)}")
            return None
    
    def quick_screenshot_for_ai(self):
        """
        快速截图并转换为API可用的格式
        
        Returns:
            str: base64编码的图像字符串，可直接用于API调用
        """
        screenshot = self.capture_full_screen(save_to_file=False)
        if screenshot:
            return self.image_to_base64(screenshot)
        return None

class ScreenRegionSelector:
    """屏幕区域选择器 - 允许用户选择特定区域进行截图"""
    
    def __init__(self, callback=None):
        self.callback = callback
        self.start_x = None
        self.start_y = None
        self.rect_id = None
        
    def select_region(self):
        """开始区域选择"""
        # 创建全屏透明窗口
        self.root = tk.Toplevel()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='black')
        
        # 创建画布
        self.canvas = tk.Canvas(
            self.root, 
            highlightthickness=0, 
            bg='black'
        )
        self.canvas.pack(fill='both', expand=True)
        
        # 绑定鼠标事件
        self.canvas.bind('<Button-1>', self.start_selection)
        self.canvas.bind('<B1-Motion>', self.update_selection)
        self.canvas.bind('<ButtonRelease-1>', self.end_selection)
        self.canvas.bind('<Escape>', lambda e: self.cancel_selection())
        
        # 显示提示信息
        self.canvas.create_text(
            self.root.winfo_screenwidth() // 2,
            50,
            text="按住鼠标左键拖拽选择区域，按ESC取消",
            fill='white',
            font=('Arial', 16)
        )
        
        self.canvas.focus_set()
    
    def start_selection(self, event):
        """开始选择"""
        self.start_x = event.x
        self.start_y = event.y
    
    def update_selection(self, event):
        """更新选择框"""
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        
        self.rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y,
            outline='red', width=2
        )
    
    def end_selection(self, event):
        """结束选择"""
        if self.start_x and self.start_y:
            # 计算选择区域
            bbox = (
                min(self.start_x, event.x),
                min(self.start_y, event.y),
                max(self.start_x, event.x),
                max(self.start_y, event.y)
            )
            
            self.root.destroy()
            
            # 调用回调函数
            if self.callback:
                self.callback(bbox)
    
    def cancel_selection(self):
        """取消选择"""
        self.root.destroy()
