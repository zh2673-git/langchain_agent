"""
OpenWebUI工具: weather_query
查询指定地点的天气信息

自动生成的工具文件 - 请勿手动修改
"""

from typing import Any, Dict
import json


class Tools:
    def __init__(self):
        self.citation = true

    def weather_query(self, location: str, units: str = "metric") -> str:
        """
        查询指定地点的天气信息
        
        :param location: 地点名称，例如 '北京' 或 'Beijing'
        :param units: 温度单位
        """
        try:
            # 调用LangChain后端API
            import requests
            
            url = "http://langchain-backend:8000/v1/tools/execute"
            payload = {
                "tool_name": "weather_query",
                "parameters": {"location": location, "units": units}
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
class Weather_QueryTool:
    """
    OpenWebUI weather_query 工具
    """
    
    def __init__(self):
        self.tools = Tools()
    
    def get_tools(self):
        """返回工具定义"""
        return {
            "weather_query": {
                "callable": self.tools.weather_query,
                "citation": self.tools.citation,
                "description": "查询指定地点的天气信息",
                "parameters": {
                "type": "object",
                "properties": {
                                "location": {
                                                "type": "string",
                                                "description": "地点名称，例如 '北京' 或 'Beijing'"
                                },
                                "units": {
                                                "type": "string",
                                                "description": "温度单位",
                                                "enum": [
                                                                "metric",
                                                                "imperial"
                                                ],
                                                "default": "metric"
                                }
                },
                "required": [
                                "location"
                ]
}
            }
        }


# 实例化工具
weather_query_tool = Weather_QueryTool()
tools = weather_query_tool.get_tools()
