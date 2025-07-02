"""
OpenWebUI工具: list_processor
处理列表数据，支持排序、去重、计数等操作

自动生成的工具文件 - 请勿手动修改
"""

from typing import Any, Dict
import json


class Tools:
    def __init__(self):
        self.citation = true

    def list_processor(self, items_str: str, operation: str = "sort") -> str:
        """
        处理列表数据，支持排序、去重、计数等操作
        
        :param items_str: 列表项，用逗号分隔，如 'apple,banana,orange'
        :param operation: 操作类型
        """
        try:
            # 调用LangChain后端API
            import requests
            
            url = "http://langchain-backend:8000/v1/tools/execute"
            payload = {
                "tool_name": "list_processor",
                "parameters": {"items_str": items_str, "operation": operation}
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
class List_ProcessorTool:
    """
    OpenWebUI list_processor 工具
    """
    
    def __init__(self):
        self.tools = Tools()
    
    def get_tools(self):
        """返回工具定义"""
        return {
            "list_processor": {
                "callable": self.tools.list_processor,
                "citation": self.tools.citation,
                "description": "处理列表数据，支持排序、去重、计数等操作",
                "parameters": {
                "type": "object",
                "properties": {
                                "items_str": {
                                                "type": "string",
                                                "description": "列表项，用逗号分隔，如 'apple,banana,orange'"
                                },
                                "operation": {
                                                "type": "string",
                                                "description": "操作类型",
                                                "enum": [
                                                                "sort",
                                                                "reverse",
                                                                "unique",
                                                                "count",
                                                                "shuffle"
                                                ],
                                                "default": "sort"
                                }
                },
                "required": [
                                "items_str"
                ]
}
            }
        }


# 实例化工具
list_processor_tool = List_ProcessorTool()
tools = list_processor_tool.get_tools()
