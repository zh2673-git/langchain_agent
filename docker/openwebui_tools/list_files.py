"""
OpenWebUI工具: list_files
列出目录中的文件和子目录

自动生成的工具文件 - 请勿手动修改
"""

from typing import Any, Dict
import json


class Tools:
    def __init__(self):
        self.citation = true

    def list_files(self, directory: str = ".") -> str:
        """
        列出目录中的文件和子目录
        
        :param directory: 目录路径，相对于workspace目录
        """
        try:
            # 调用LangChain后端API
            import requests
            
            url = "http://langchain-backend:8000/v1/tools/execute"
            payload = {
                "tool_name": "list_files",
                "parameters": {"directory": directory}
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
class List_FilesTool:
    """
    OpenWebUI list_files 工具
    """
    
    def __init__(self):
        self.tools = Tools()
    
    def get_tools(self):
        """返回工具定义"""
        return {
            "list_files": {
                "callable": self.tools.list_files,
                "citation": self.tools.citation,
                "description": "列出目录中的文件和子目录",
                "parameters": {
                "type": "object",
                "properties": {
                                "directory": {
                                                "type": "string",
                                                "description": "目录路径，相对于workspace目录",
                                                "default": "."
                                }
                },
                "required": []
}
            }
        }


# 实例化工具
list_files_tool = List_FilesTool()
tools = list_files_tool.get_tools()
