"""
OpenWebUI工具: format_timestamp
将时间戳转换为可读的时间格式

自动生成的工具文件 - 请勿手动修改
"""

from typing import Any, Dict
import json


class Tools:
    def __init__(self):
        self.citation = true

    def format_timestamp(self, timestamp: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        将时间戳转换为可读的时间格式
        
        :param timestamp: Unix时间戳（秒）
        :param format_str: 时间格式字符串，例如 '%Y-%m-%d %H:%M:%S'
        """
        try:
            # 调用LangChain后端API
            import requests
            
            url = "http://langchain-backend:8000/v1/tools/execute"
            payload = {
                "tool_name": "format_timestamp",
                "parameters": {"timestamp": timestamp, "format_str": format_str}
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
class Format_TimestampTool:
    """
    OpenWebUI format_timestamp 工具
    """
    
    def __init__(self):
        self.tools = Tools()
    
    def get_tools(self):
        """返回工具定义"""
        return {
            "format_timestamp": {
                "callable": self.tools.format_timestamp,
                "citation": self.tools.citation,
                "description": "将时间戳转换为可读的时间格式",
                "parameters": {
                "type": "object",
                "properties": {
                                "timestamp": {
                                                "type": "string",
                                                "description": "Unix时间戳（秒）"
                                },
                                "format_str": {
                                                "type": "string",
                                                "description": "时间格式字符串，例如 '%Y-%m-%d %H:%M:%S'",
                                                "default": "%Y-%m-%d %H:%M:%S"
                                }
                },
                "required": [
                                "timestamp"
                ]
}
            }
        }


# 实例化工具
format_timestamp_tool = Format_TimestampTool()
tools = format_timestamp_tool.get_tools()
