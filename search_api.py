import requests
import json
from typing import List, Dict

class SearchAPI:
    def __init__(self):
        """初始化搜索API"""
        # 使用免费的搜索API - DuckDuckGo Instant Answer API
        self.search_url = "https://api.duckduckgo.com/"
        self.serper_url = "https://google.serper.dev/search"
        
    def search_duckduckgo(self, query: str) -> str:
        """使用DuckDuckGo搜索"""
        try:
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = requests.get(self.search_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # 优先使用Abstract（摘要）
                if data.get('Abstract'):
                    return data['Abstract']
                
                # 然后使用Definition（定义）
                if data.get('Definition'):
                    return data['Definition']
                
                # 最后使用RelatedTopics的第一个
                if data.get('RelatedTopics') and len(data['RelatedTopics']) > 0:
                    first_topic = data['RelatedTopics'][0]
                    if isinstance(first_topic, dict) and 'Text' in first_topic:
                        return first_topic['Text']
                
                return None
            
            return None
            
        except Exception as e:
            print(f"DuckDuckGo搜索失败: {str(e)}")
            return None
    
    def search_web(self, query: str) -> str:
        """综合网络搜索 - 主要搜索方法"""
        try:
            # 首先尝试DuckDuckGo
            result = self.search_duckduckgo(query)
            if result:
                return result
            
            # 如果DuckDuckGo没有结果，返回提示信息
            return f"未找到关于'{query}'的详细信息。建议您换个关键词搜索，或者描述更具体的问题。"
            
        except Exception as e:
            return f"搜索时出现错误: {str(e)}"
    
    def is_search_query(self, text: str) -> bool:
        """判断是否为搜索查询"""
        search_keywords = [
            '搜索', 'search', '查找', '找', '查询', 
            '你知道', '知道', '了解', '听说过',
            '什么是', '是什么', '怎么', '如何',
            '游戏攻略', '攻略', '策略', '技巧',
            '怎么玩', '怎么做', '方法'
        ]
        
        text_lower = text.lower()
        for keyword in search_keywords:
            if keyword in text_lower:
                return True
        
        return False
    
    def extract_search_query(self, text: str) -> str:
        """从用户输入中提取搜索关键词"""
        # 移除常见的前缀词
        prefixes_to_remove = [
            '搜索', 'search', '查找', '找一下', '查询',
            '你知道', '知道不知道', '听说过', 
            '什么是', '是什么', '告诉我',
            '我想了解', '给我找', '帮我查'
        ]
        
        cleaned_query = text.strip()
        
        # 移除问号和感叹号
        cleaned_query = cleaned_query.replace('？', '').replace('?', '').replace('！', '').replace('!', '')
        
        # 移除前缀词
        for prefix in prefixes_to_remove:
            if cleaned_query.startswith(prefix):
                cleaned_query = cleaned_query[len(prefix):].strip()
                break
        
        # 如果查询为空，返回原文本
        if not cleaned_query:
            return text
            
        return cleaned_query
