"""
OpenWebUI工具: read_file
读取文件内容（限制在workspace目录内）

自动生成的工具文件 - 请勿手动修改
"""

from typing import Any, Dict
import json


class Tools:
    def __init__(self):
        self.citation = true

    def read_file(self, file_path: str, encoding: str = "utf-8") -> str:
        """
        读取文件内容（限制在workspace目录内）
        
        :param file_path: 文件路径，相对于workspace目录
        :param encoding: 文件编码
        """
        try:
            # 调用LangChain后端API
            import requests
            
            url = "http://langchain-backend:8000/v1/tools/execute"
            payload = {
                "tool_name": "read_file",
                "parameters": {"file_path": file_path, "encoding": encoding}
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
class Read_FileTool:
    """
    OpenWebUI read_file 工具
    """
    
    def __init__(self):
        self.tools = Tools()
    
    def get_tools(self):
        """返回工具定义"""
        return {
            "read_file": {
                "callable": self.tools.read_file,
                "citation": self.tools.citation,
                "description": "读取文件内容（限制在workspace目录内）",
                "parameters": {
                "type": "object",
                "properties": {
                                "file_path": {
                                                "type": "string",
                                                "description": "文件路径，相对于workspace目录"
                                },
                                "encoding": {
                                                "type": "string",
                                                "description": "文件编码",
                                                "default": "utf-8"
                                }
                },
                "required": [
                                "file_path"
                ]
}
            }
        }


# 实例化工具
read_file_tool = Read_FileTool()
tools = read_file_tool.get_tools()
