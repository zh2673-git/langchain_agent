"""
OpenWebUI工具: date_calculator
日期计算器，支持日期加减和差值计算

自动生成的工具文件 - 请勿手动修改
"""

from typing import Any, Dict
import json


class Tools:
    def __init__(self):
        self.citation = true

    def date_calculator(self, start_date: str, operation: str = "add", days: int = 1) -> str:
        """
        日期计算器，支持日期加减和差值计算
        
        :param start_date: 起始日期，格式: YYYY-MM-DD
        :param operation: 操作类型
        :param days: 天数
        """
        try:
            # 调用LangChain后端API
            import requests
            
            url = "http://langchain-backend:8000/v1/tools/execute"
            payload = {
                "tool_name": "date_calculator",
                "parameters": {"start_date": start_date, "operation": operation, "days": days}
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
class Date_CalculatorTool:
    """
    OpenWebUI date_calculator 工具
    """
    
    def __init__(self):
        self.tools = Tools()
    
    def get_tools(self):
        """返回工具定义"""
        return {
            "date_calculator": {
                "callable": self.tools.date_calculator,
                "citation": self.tools.citation,
                "description": "日期计算器，支持日期加减和差值计算",
                "parameters": {
                "type": "object",
                "properties": {
                                "start_date": {
                                                "type": "string",
                                                "description": "起始日期，格式: YYYY-MM-DD"
                                },
                                "operation": {
                                                "type": "string",
                                                "description": "操作类型",
                                                "enum": [
                                                                "add",
                                                                "subtract",
                                                                "diff"
                                                ],
                                                "default": "add"
                                },
                                "days": {
                                                "type": "integer",
                                                "description": "天数",
                                                "default": 1
                                }
                },
                "required": [
                                "start_date"
                ]
}
            }
        }


# 实例化工具
date_calculator_tool = Date_CalculatorTool()
tools = date_calculator_tool.get_tools()
