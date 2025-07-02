"""
OpenWebUI工具: string_processor
字符串处理工具，支持大小写转换、反转和长度计算

自动生成的工具文件 - 请勿手动修改
"""

from typing import Any, Dict
import json


class Tools:
    def __init__(self):
        self.citation = true

    def string_processor(self, text: str, operation: str = "upper") -> str:
        """
        字符串处理工具，支持大小写转换、反转和长度计算
        
        :param text: 要处理的文本
        :param operation: 操作类型
        """
        try:
            # 调用LangChain后端API
            import requests
            
            url = "http://langchain-backend:8000/v1/tools/execute"
            payload = {
                "tool_name": "string_processor",
                "parameters": {"text": text, "operation": operation}
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
class String_ProcessorTool:
    """
    OpenWebUI string_processor 工具
    """
    
    def __init__(self):
        self.tools = Tools()
    
    def get_tools(self):
        """返回工具定义"""
        return {
            "string_processor": {
                "callable": self.tools.string_processor,
                "citation": self.tools.citation,
                "description": "字符串处理工具，支持大小写转换、反转和长度计算",
                "parameters": {
                "type": "object",
                "properties": {
                                "text": {
                                                "type": "string",
                                                "description": "要处理的文本"
                                },
                                "operation": {
                                                "type": "string",
                                                "description": "操作类型",
                                                "enum": [
                                                                "upper",
                                                                "lower",
                                                                "reverse",
                                                                "length"
                                                ],
                                                "default": "upper"
                                }
                },
                "required": [
                                "text"
                ]
}
            }
        }


# 实例化工具
string_processor_tool = String_ProcessorTool()
tools = string_processor_tool.get_tools()
