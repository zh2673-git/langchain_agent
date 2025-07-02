"""
OpenWebUI工具: calculator
计算数学表达式，支持基本的四则运算、幂运算和取模运算

自动生成的工具文件 - 请勿手动修改
"""

from typing import Any, Dict
import json


class Tools:
    def __init__(self):
        self.citation = true

    def calculator(self, expression: str) -> str:
        """
        计算数学表达式，支持基本的四则运算、幂运算和取模运算
        
        :param expression: 要计算的数学表达式，例如 '2 + 3 * 4'
        """
        try:
            # 调用LangChain后端API
            import requests
            
            url = "http://langchain-backend:8000/v1/tools/execute"
            payload = {
                "tool_name": "calculator",
                "parameters": {"expression": expression}
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
class CalculatorTool:
    """
    OpenWebUI calculator 工具
    """
    
    def __init__(self):
        self.tools = Tools()
    
    def get_tools(self):
        """返回工具定义"""
        return {
            "calculator": {
                "callable": self.tools.calculator,
                "citation": self.tools.citation,
                "description": "计算数学表达式，支持基本的四则运算、幂运算和取模运算",
                "parameters": {
                "type": "object",
                "properties": {
                                "expression": {
                                                "type": "string",
                                                "description": "要计算的数学表达式，例如 '2 + 3 * 4'"
                                }
                },
                "required": [
                                "expression"
                ]
}
            }
        }


# 实例化工具
calculator_tool = CalculatorTool()
tools = calculator_tool.get_tools()
