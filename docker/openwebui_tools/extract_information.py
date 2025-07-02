"""
OpenWebUI工具: extract_information
从文本中提取特定信息，如邮箱、网址、电话号码等

自动生成的工具文件 - 请勿手动修改
"""

from typing import Any, Dict
import json


class Tools:
    def __init__(self):
        self.citation = true

    def extract_information(self, text: str, info_type: str = "emails") -> str:
        """
        从文本中提取特定信息，如邮箱、网址、电话号码等
        
        :param text: 要分析的文本
        :param info_type: 信息类型
        """
        try:
            # 调用LangChain后端API
            import requests
            
            url = "http://langchain-backend:8000/v1/tools/execute"
            payload = {
                "tool_name": "extract_information",
                "parameters": {"text": text, "info_type": info_type}
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
class Extract_InformationTool:
    """
    OpenWebUI extract_information 工具
    """
    
    def __init__(self):
        self.tools = Tools()
    
    def get_tools(self):
        """返回工具定义"""
        return {
            "extract_information": {
                "callable": self.tools.extract_information,
                "citation": self.tools.citation,
                "description": "从文本中提取特定信息，如邮箱、网址、电话号码等",
                "parameters": {
                "type": "object",
                "properties": {
                                "text": {
                                                "type": "string",
                                                "description": "要分析的文本"
                                },
                                "info_type": {
                                                "type": "string",
                                                "description": "信息类型",
                                                "enum": [
                                                                "emails",
                                                                "urls",
                                                                "phones",
                                                                "numbers"
                                                ],
                                                "default": "emails"
                                }
                },
                "required": [
                                "text"
                ]
}
            }
        }


# 实例化工具
extract_information_tool = Extract_InformationTool()
tools = extract_information_tool.get_tools()
