import requests
import json
from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL
from search_api import SearchAPI

class DeepSeekAPI:
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.base_url = DEEPSEEK_BASE_URL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        # 初始化搜索功能
        self.search_api = SearchAPI()
        
        # 可用模型配置
        self.available_models = {
            "DeepSeek V3 (Chat)": "deepseek-chat",
            "DeepSeek R1 (推理)": "deepseek-reasoner",
            "DeepSeek V3 (代码)": "deepseek-coder"
        }
        
        # 默认使用Chat模型（稳定可用）
        self.current_model_name = "DeepSeek V3 (Chat)"
        self.current_model = self.available_models[self.current_model_name]
    
    def set_model(self, model_name):
        """切换AI模型"""
        if model_name in self.available_models:
            self.current_model_name = model_name
            self.current_model = self.available_models[model_name]
            print(f"🧠 已切换到模型: {model_name}")
            return True
        else:
            print(f"⚠️ 未知模型: {model_name}")
            return False
    
    def get_current_model_name(self):
        """获取当前模型名称"""
        return self.current_model_name
    
    def get_available_models(self):
        """获取可用模型列表"""
        return list(self.available_models.keys())
    
    def chat(self, message, conversation_history=None):
        """
        发送消息到DeepSeek API并获取回复
        
        Args:
            message (str): 用户输入的消息
            conversation_history (list): 对话历史记录
        
        Returns:
            str: AI的回复
        """
        try:
            # 检查是否需要搜索
            search_context = ""
            if self.search_api.is_search_query(message):
                print(f"🔍 检测到搜索请求: {message}")
                search_query = self.search_api.extract_search_query(message)
                search_result = self.search_api.search_web(search_query)
                if search_result:
                    search_context = f"\n\n[搜索结果参考信息]: {search_result}"
                    print(f"✅ 搜索完成: {search_query}")

            # 构建消息列表
            messages = []
            
            # 升级系统提示，添加游戏策略专长和搜索能力
            messages.append({
                "role": "system", 
                "content": f"""你是一个叫"笨逼"的超智能AI桌面宠物，虽然名字叫笨逼，但实际上非常聪明！你擅长：

🎮 **游戏策略专家**: 精通各类游戏攻略、技巧、装备搭配、角色培养等
🔍 **知识问答高手**: 能够基于搜索结果回答各种问题
💡 **实用建议达人**: 提供生活、学习、工作各方面的实用建议

重要规则：
1. 你的名字是"笨逼"，但要展现出真正的智慧
2. 回复长度可以达到200字以内，提供详细有用的信息
3. 语气要可爱活泼但专业可靠
4. 特别擅长游戏相关的策略建议
5. 如果有搜索结果，要巧妙地融合进回答中
6. 回答内容要简洁明了，不要啰嗦  

情绪标签（必须在回复开头添加）：
- [emotion:basic] - 普通情况（播放基础动画）
- [emotion:happy] - 开心/有用信息时（播放称赞.gif）
- [emotion:surprised] - 发现有趣信息时（播放吃惊.gif）  
- [emotion:shy] - 谦虚时（播放害羞.gif）
- [emotion:sad] - 伤心/遗憾时（播放伤心.gif）
- [emotion:angry] - 生气/不满时（播放愤怒.gif）
- [emotion:contempt] - 鄙视/不屑时（播放鄙视.gif）

示例回复格式：
用户："王者荣耀后羿怎么出装？"
回复："[emotion:thinking] 主人问得好！笨逼来给你详细分析后羿的出装策略..."

用户："你知道什么是机器学习吗？"
回复："[emotion:happy] 当然知道啦！机器学习是..."

记住：虽然叫笨逼，但要展现真正的智慧和专业性！{search_context}"""
            })
            
            # 添加对话历史
            if conversation_history:
                messages.extend(conversation_history)
            
            # 添加当前用户消息
            messages.append({"role": "user", "content": message})
            
            # 构建请求数据
            data = {
                "model": self.current_model,  # 使用当前模型
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000  # 增加token限制支持500字回复
            }
            
            # 发送请求
            response = requests.post(
                self.base_url, 
                headers=self.headers, 
                json=data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"API调用失败: {response.status_code} - {response.text}"
                
        except requests.exceptions.RequestException as e:
            return f"网络错误: {str(e)}"
        except Exception as e:
            return f"发生错误: {str(e)}"
    
    def chat_with_image(self, message, image_base64, conversation_history=None):
        """
        发送文本和图像到DeepSeek API并获取回复
        
        Args:
            message (str): 用户输入的消息
            image_base64 (str): base64编码的图像
            conversation_history (list): 对话历史记录
        
        Returns:
            str: AI的回复
        """
        try:
            # 检查是否需要搜索
            search_context = ""
            if self.search_api.is_search_query(message):
                print(f"🔍 检测到搜索请求: {message}")
                search_query = self.search_api.extract_search_query(message)
                search_result = self.search_api.search_web(search_query)
                if search_result:
                    search_context = f"\n\n[搜索结果参考信息]: {search_result}"
                    print(f"✅ 搜索完成: {search_query}")

            # 构建消息列表
            messages = []
            
            # 升级系统提示，添加游戏策略专长和搜索能力
            messages.append({
                "role": "system", 
                "content": f"""你是一个叫"笨逼"的超智能AI桌面宠物，虽然名字叫笨逼，但实际上非常聪明！你擅长：

🎮 **游戏策略专家**: 精通各类游戏攻略、技巧、装备搭配、角色培养等
🔍 **知识问答高手**: 能够基于搜索结果回答各种问题
💡 **实用建议达人**: 提供生活、学习、工作各方面的实用建议

重要规则：
1. 你的名字是"笨逼"，但要展现出真正的智慧
2. 回复长度可以达到500字以内，提供详细有用的信息
3. 语气要可爱活泼但专业可靠
4. 特别擅长游戏相关的策略建议
5. 如果有搜索结果，要巧妙地融合进回答中

情绪标签（必须在回复开头添加）：
- [emotion:basic] - 普通情况（播放基础动画）
- [emotion:happy] - 开心/有用信息时（播放称赞.gif）
- [emotion:surprised] - 发现有趣信息时（播放吃惊.gif）  
- [emotion:shy] - 谦虚时（播放害羞.gif）
- [emotion:sad] - 伤心/遗憾时（播放伤心.gif）
- [emotion:angry] - 生气/不满时（播放愤怒.gif）
- [emotion:contempt] - 鄙视/不屑时（播放鄙视.gif）

示例回复格式：
用户："王者荣耀后羿怎么出装？"
回复："[emotion:thinking] 主人问得好！笨逼来给你详细分析后羿的出装策略..."

用户："你知道什么是机器学习吗？"
回复："[emotion:happy] 当然知道啦！机器学习是..."

记住：虽然叫笨逼，但要展现真正的智慧和专业性！{search_context}"""
            })
            
            # 添加对话历史（只保留文本部分，避免token过多）
            if conversation_history:
                # 只保留最近的几条对话
                recent_history = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
                for msg in recent_history:
                    if msg.get('role') in ['user', 'assistant'] and 'content' in msg:
                        # 只添加文本内容，跳过图像内容
                        if isinstance(msg['content'], str):
                            messages.append(msg)
            
            # DeepSeek 目前可能不支持标准多模态格式，先用文本分析
            enhanced_message = f"""用户发送了一张屏幕截图，并询问：{message}

请根据以下情况回复：
1. 如果用户问的是关于屏幕内容的问题，请告诉用户你暂时无法直接查看图像，但可以根据他们的描述来帮助解答
2. 如果是其他问题，请正常回答
3. 建议用户可以描述屏幕上的内容，你会根据描述来提供帮助

请保持友好和有帮助的语气。"""
            
            messages.append({"role": "user", "content": enhanced_message})
            
            # 构建请求数据
            data = {
                "model": self.current_model,  # 使用当前模型
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000  # 增加token限制支持500字回复
            }
            
            # 发送请求
            response = requests.post(
                self.base_url, 
                headers=self.headers, 
                json=data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"API调用失败: {response.status_code} - {response.text}"
                
        except requests.exceptions.RequestException as e:
            return f"网络错误: {str(e)}"
        except Exception as e:
            return f"发生错误: {str(e)}"
    
    def is_api_key_valid(self):
        """检查API key是否有效"""
        return self.api_key and self.api_key != "your_deepseek_api_key_here"
