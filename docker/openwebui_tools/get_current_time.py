"""
OpenWebUI工具: get_current_time
获取当前日期和时间，支持不同时区

自动生成的工具文件 - 请勿手动修改
"""

from typing import Any, Dict
import json


class Tools:
    def __init__(self):
        self.citation = true

    def get_current_time(self, timezone_name: str = "Asia/Shanghai") -> str:
        """
        获取当前日期和时间，支持不同时区
        
        :param timezone_name: 时区名称，例如 'Asia/Shanghai', 'UTC'
        """
        try:
            # 调用LangChain后端API
            import requests
            
            url = "http://langchain-backend:8000/v1/tools/execute"
            payload = {
                "tool_name": "get_current_time",
                "parameters": {"timezone_name": timezone_name}
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
class Get_Current_TimeTool:
    """
    OpenWebUI get_current_time 工具
    """
    
    def __init__(self):
        self.tools = Tools()
    
    def get_tools(self):
        """返回工具定义"""
        return {
            "get_current_time": {
                "callable": self.tools.get_current_time,
                "citation": self.tools.citation,
                "description": "获取当前日期和时间，支持不同时区",
                "parameters": {
                "type": "object",
                "properties": {
                                "timezone_name": {
                                                "type": "string",
                                                "description": "时区名称，例如 'Asia/Shanghai', 'UTC'",
                                                "default": "Asia/Shanghai"
                                }
                },
                "required": []
}
            }
        }


# 实例化工具
get_current_time_tool = Get_Current_TimeTool()
tools = get_current_time_tool.get_tools()
