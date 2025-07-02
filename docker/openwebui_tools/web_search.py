"""
OpenWebUI工具: web_search
搜索网络信息，获取实时数据和答案

自动生成的工具文件 - 请勿手动修改
"""

from typing import Any, Dict
import json


class Tools:
    def __init__(self):
        self.citation = true

    def web_search(self, query: str, num_results: int = 5) -> str:
        """
        搜索网络信息，获取实时数据和答案
        
        :param query: 搜索查询
        :param num_results: 返回结果数量，默认5个
        """
        try:
            # 调用LangChain后端API
            import requests
            
            url = "http://langchain-backend:8000/v1/tools/execute"
            payload = {
                "tool_name": "web_search",
                "parameters": {"query": query, "num_results": num_results}
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
class Web_SearchTool:
    """
    OpenWebUI web_search 工具
    """
    
    def __init__(self):
        self.tools = Tools()
    
    def get_tools(self):
        """返回工具定义"""
        return {
            "web_search": {
                "callable": self.tools.web_search,
                "citation": self.tools.citation,
                "description": "搜索网络信息，获取实时数据和答案",
                "parameters": {
                "type": "object",
                "properties": {
                                "query": {
                                                "type": "string",
                                                "description": "搜索查询"
                                },
                                "num_results": {
                                                "type": "integer",
                                                "description": "返回结果数量，默认5个",
                                                "default": 5,
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
web_search_tool = Web_SearchTool()
tools = web_search_tool.get_tools()
