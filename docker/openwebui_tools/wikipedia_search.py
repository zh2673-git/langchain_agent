"""
OpenWebUI工具: wikipedia_search
搜索Wikipedia文章，获取百科知识

自动生成的工具文件 - 请勿手动修改
"""

from typing import Any, Dict
import json


class Tools:
    def __init__(self):
        self.citation = true

    def wikipedia_search(self, query: str, max_results: int = 3) -> str:
        """
        搜索Wikipedia文章，获取百科知识
        
        :param query: 搜索查询，例如 '人工智能' 或 'Python编程'
        :param max_results: 最大结果数量，默认3个
        """
        try:
            # 调用LangChain后端API
            import requests
            
            url = "http://langchain-backend:8000/v1/tools/execute"
            payload = {
                "tool_name": "wikipedia_search",
                "parameters": {"query": query, "max_results": max_results}
            }
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("result", "执行成功")
            else:
                return f"工具执行失败: {response.status_code}"
                
        except Exception as e:
            return f"工具执行错误: {str(e)}"


# OpenWebUI工具规范
class Wikipedia_SearchTool:
    """
    OpenWebUI wikipedia_search 工具
    """
    
    def __init__(self):
        self.tools = Tools()
    
    def get_tools(self):
        """返回工具定义"""
        return {
            "wikipedia_search": {
                "callable": self.tools.wikipedia_search,
                "citation": self.tools.citation,
                "description": "搜索Wikipedia文章，获取百科知识",
                "parameters": {
                "type": "object",
                "properties": {
                                "query": {
                                                "type": "string",
                                                "description": "搜索查询，例如 '人工智能' 或 'Python编程'"
                                },
                                "max_results": {
                                                "type": "integer",
                                                "description": "最大结果数量，默认3个",
                                                "default": 3,
                                                "minimum": 1,
                                                "maximum": 10
                                }
                },
                "required": [
                                "query"
                ]
}
            }
        }


# 实例化工具
wikipedia_search_tool = Wikipedia_SearchTool()
tools = wikipedia_search_tool.get_tools()
