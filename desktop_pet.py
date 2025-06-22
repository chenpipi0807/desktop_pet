import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
from deepseek_api import DeepSeekAPI
from screen_capture import ScreenCapture, ScreenRegionSelector
from config import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE
from PIL import Image, ImageTk
import os

class DesktopPet:
    def __init__(self):
        self.root = tk.Tk()
        self.api = DeepSeekAPI()
        self.screen_capture = ScreenCapture()
        self.conversation_history = []
        self.screenshot_mode = False  # 是否启用截图模式
        
        # 加载桌宠图片
        self.load_pet_image()
        
        self.setup_window()
        self.setup_ui()
        
        # 检查API key
        if not self.api.is_api_key_valid():
            messagebox.showwarning(
                "API Key 未设置", 
                "请在config.py中设置你的DeepSeek API Key！"
            )
    
    def load_pet_image(self):
        """加载桌宠图片"""
        try:
            image_path = os.path.join("image", "base.png")
            if os.path.exists(image_path):
                # 加载并调整图片大小
                self.pet_image = Image.open(image_path)
                # 调整图片大小，保持宽高比
                pet_size = (80, 80)
                self.pet_image = self.pet_image.resize(pet_size, Image.Resampling.LANCZOS)
                self.pet_photo = ImageTk.PhotoImage(self.pet_image)
            else:
                self.pet_photo = None
                print(f"桌宠图片未找到: {image_path}")
        except Exception as e:
            self.pet_photo = None
            print(f"加载桌宠图片失败: {str(e)}")
    
    def setup_window(self):
        """设置窗口属性"""
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        
        # 设置窗口置顶
        self.root.attributes('-topmost', True)
        
        # 设置窗口可以拖动
        self.root.bind('<Button-1>', self.start_drag)
        self.root.bind('<B1-Motion>', self.drag_window)
        
        # 设置窗口样式
        self.root.configure(bg='#f8f9fa')
    
    def setup_ui(self):
        """设置用户界面"""
        # 标题栏 - 包含桌宠图片
        title_frame = tk.Frame(self.root, bg='#4a90e2', height=50)
        title_frame.pack(fill='x', pady=(0, 5))
        title_frame.pack_propagate(False)  # 防止frame自动调整大小
        
        # 桌宠图片和标题
        pet_title_frame = tk.Frame(title_frame, bg='#4a90e2')
        pet_title_frame.pack(expand=True, fill='both')
        
        if self.pet_photo:
            pet_label = tk.Label(
                pet_title_frame,
                image=self.pet_photo,
                bg='#4a90e2'
            )
            pet_label.pack(side='left', padx=(10, 5), pady=5)
        
        title_label = tk.Label(
            pet_title_frame, 
            text="🤖 AI桌宠", 
            bg='#4a90e2', 
            fg='white', 
            font=('微软雅黑', 12, 'bold')
        )
        title_label.pack(side='left', pady=5)
        
        # 添加一个可爱的状态指示器
        self.status_label = tk.Label(
            pet_title_frame,
            text="😊",
            bg='#4a90e2',
            fg='white',
            font=('微软雅黑', 16)
        )
        self.status_label.pack(side='right', padx=(5, 10), pady=5)
        
        # 对话显示区域
        chat_frame = tk.Frame(self.root, bg='#f8f9fa')
        chat_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=('微软雅黑', 10),
            bg='#ffffff',
            fg='#333333',
            state=tk.DISABLED,
            relief='solid',
            borderwidth=1
        )
        self.chat_display.pack(fill='both', expand=True)
        
        # 输入区域
        input_frame = tk.Frame(self.root, bg='#f8f9fa')
        input_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.input_entry = tk.Entry(
            input_frame,
            font=('微软雅黑', 10),
            relief='solid',
            borderwidth=1,
            bg='white'
        )
        self.input_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.input_entry.bind('<Return>', self.send_message)
        
        self.send_button = tk.Button(
            input_frame,
            text="发送",
            font=('微软雅黑', 10),
            bg='#4a90e2',
            fg='white',
            relief='flat',
            command=self.send_message,
            cursor='hand2'
        )
        self.send_button.pack(side='right')
        
        # 控制按钮区域
        control_frame = tk.Frame(self.root, bg='#f8f9fa')
        control_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # 左侧按钮
        left_buttons = tk.Frame(control_frame, bg='#f8f9fa')
        left_buttons.pack(side='left')
        
        self.clear_button = tk.Button(
            left_buttons,
            text="🗑️ 清空",
            font=('微软雅黑', 9),
            bg='#ff6b6b',
            fg='white',
            relief='flat',
            command=self.clear_chat,
            cursor='hand2'
        )
        self.clear_button.pack(side='left', padx=(0, 5))
        
        # 截图相关按钮
        self.screenshot_button = tk.Button(
            left_buttons,
            text="📸 截图聊天",
            font=('微软雅黑', 9),
            bg='#4ecdc4',
            fg='white',
            relief='flat',
            command=self.toggle_screenshot_mode,
            cursor='hand2'
        )
        self.screenshot_button.pack(side='left', padx=(0, 5))
        
        self.manual_screenshot_button = tk.Button(
            left_buttons,
            text="🖼️ 立即截图",
            font=('微软雅黑', 9),
            bg='#45b7d1',
            fg='white',
            relief='flat',
            command=self.take_screenshot_and_ask,
            cursor='hand2'
        )
        self.manual_screenshot_button.pack(side='left')
        
        # 右侧按钮
        right_buttons = tk.Frame(control_frame, bg='#f8f9fa')
        right_buttons.pack(side='right')
        
        self.minimize_button = tk.Button(
            right_buttons,
            text="➖",
            font=('微软雅黑', 9),
            bg='#95a5a6',
            fg='white',
            relief='flat',
            command=self.root.iconify,
            cursor='hand2'
        )
        self.minimize_button.pack(side='right')
        
        # 模式指示器
        self.mode_indicator = tk.Label(
            self.root,
            text="💬 文本聊天模式",
            font=('微软雅黑', 9),
            bg='#f8f9fa',
            fg='#666'
        )
        self.mode_indicator.pack(pady=(0, 5))
        
        # 欢迎消息
        self.add_message("AI", "你好！我是你的AI桌宠，有什么想聊的吗？🎉\n\n💡 提示：\n• 点击 '📸 截图聊天' 开启屏幕理解模式\n• 点击 '🖼️ 立即截图' 让我看看你的屏幕")
    
    def update_status_emoji(self, emoji):
        """更新状态表情"""
        self.status_label.config(text=emoji)
    
    def start_drag(self, event):
        """开始拖拽窗口"""
        self.x = event.x
        self.y = event.y
    
    def drag_window(self, event):
        """拖拽窗口"""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
    
    def add_message(self, sender, message):
        """在聊天窗口中添加消息"""
        self.chat_display.config(state=tk.NORMAL)
        
        if sender == "你":
            self.chat_display.insert(tk.END, f"\n💬 {sender}: {message}\n", 'user')
        else:
            self.chat_display.insert(tk.END, f"\n🤖 {sender}: {message}\n", 'bot')
        
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def send_message(self, event=None):
        """发送消息"""
        user_input = self.input_entry.get().strip()
        if not user_input:
            return
        
        # 清空输入框
        self.input_entry.delete(0, tk.END)
        
        # 显示用户消息
        self.add_message("你", user_input)
        
        # 禁用发送按钮，显示正在思考
        self.send_button.config(state=tk.DISABLED, text="思考中...")
        
        # 在新线程中处理API调用，避免界面卡顿
        threading.Thread(
            target=self.handle_api_response, 
            args=(user_input,), 
            daemon=True
        ).start()
    
    def handle_api_response(self, user_input):
        """处理API响应"""
        try:
            if self.screenshot_mode:
                # 截图模式：同时发送文本和图像
                image_base64 = self.screen_capture.quick_screenshot_for_ai()
                
                if image_base64:
                    response = self.api.chat_with_image(
                        user_input,
                        image_base64,
                        self.conversation_history
                    )
                else:
                    response = "抱歉，截图失败了，切换到纯文本模式回复：\n" + self.api.chat(user_input, self.conversation_history)
            else:
                # 文本模式：只发送文本
                response = self.api.chat(user_input, self.conversation_history)
            
            # 更新对话历史
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": response})
            
            # 限制对话历史长度，避免token过多
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            # 在主线程中更新UI
            self.root.after(0, lambda: self.show_response(response))
            
        except Exception as e:
            self.root.after(0, lambda: self.show_response(f"出错了: {str(e)}"))
    
    def show_response(self, response):
        """显示AI回复"""
        self.add_message("AI", response)
        
        # 恢复发送按钮
        self.send_button.config(state=tk.NORMAL, text="发送")
        
        # 让输入框重新获得焦点
        self.input_entry.focus_set()
    
    def clear_chat(self):
        """清空聊天记录"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
        # 清空对话历史
        self.conversation_history = []
        
        # 重新显示欢迎消息
        self.add_message("AI", "对话已清空，我们重新开始聊天吧！😊")
    
    def toggle_screenshot_mode(self):
        """切换截图模式"""
        self.screenshot_mode = not self.screenshot_mode
        
        if self.screenshot_mode:
            self.screenshot_button.config(
                text="📱 文本模式",
                bg='#ff9f43'
            )
            self.mode_indicator.config(
                text="📸 屏幕理解模式 - 每次发送都会截图",
                fg='#4ecdc4'
            )
            self.add_message("AI", "已切换到屏幕理解模式！现在我会在每次回复时查看你的屏幕内容。👀")
        else:
            self.screenshot_button.config(
                text="📸 截图聊天",
                bg='#4ecdc4'
            )
            self.mode_indicator.config(
                text="💬 文本聊天模式",
                fg='#666'
            )
            self.add_message("AI", "已切换到文本聊天模式！现在我只会响应你的文字消息。💬")
    
    def take_screenshot_and_ask(self):
        """立即截图并询问AI"""
        self.add_message("你", "[请求查看屏幕]")
        
        # 禁用按钮，显示正在截图
        self.manual_screenshot_button.config(state=tk.DISABLED, text="截图中...")
        
        # 在新线程中处理截图和API调用
        threading.Thread(
            target=self.handle_screenshot_request,
            args=("请帮我看看我的屏幕上有什么内容，并简单描述一下。",),
            daemon=True
        ).start()
    
    def handle_screenshot_request(self, default_message):
        """处理截图请求"""
        try:
            # 截取屏幕
            image_base64 = self.screen_capture.quick_screenshot_for_ai()
            
            if image_base64:
                # 调用多模态API
                response = self.api.chat_with_image(
                    default_message,
                    image_base64,
                    self.conversation_history
                )
                
                # 更新对话历史（只保存文本部分）
                self.conversation_history.append({"role": "user", "content": default_message})
                self.conversation_history.append({"role": "assistant", "content": response})
                
                # 限制对话历史长度
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]
                
                self.root.after(0, lambda: self.show_response(response))
            else:
                self.root.after(0, lambda: self.show_response("抱歉，截图失败了，请重试。"))
                
        except Exception as e:
            self.root.after(0, lambda: self.show_response(f"处理截图时出错: {str(e)}"))
        finally:
            # 恢复按钮状态
            self.root.after(0, lambda: self.manual_screenshot_button.config(
                state=tk.NORMAL, 
                text="🖼️ 立即截图"
            ))
    
    def run(self):
        """启动桌宠"""
        self.root.mainloop()

if __name__ == "__main__":
    pet = DesktopPet()
    pet.run()
