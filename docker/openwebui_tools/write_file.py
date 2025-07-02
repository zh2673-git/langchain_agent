"""
OpenWebUI工具: write_file
写入文件内容（限制在workspace目录内）

自动生成的工具文件 - 请勿手动修改
"""

from typing import Any, Dict
import json


class Tools:
    def __init__(self):
        self.citation = true

    def write_file(self, file_path: str, content: str, encoding: str = "utf-8") -> str:
        """
        写入文件内容（限制在workspace目录内）
        
        :param file_path: 文件路径，相对于workspace目录
        :param content: 要写入的内容
        :param encoding: 文件编码
        """
        try:
            # 调用LangChain后端API
            import requests
            
            url = "http://langchain-backend:8000/v1/tools/execute"
            payload = {
                "tool_name": "write_file",
                "parameters": {"file_path": file_path, "content": content, "encoding": encoding}
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
class Write_FileTool:
    """
    OpenWebUI write_file 工具
    """
    
    def __init__(self):
        self.tools = Tools()
    
    def get_tools(self):
        """返回工具定义"""
        return {
            "write_file": {
                "callable": self.tools.write_file,
                "citation": self.tools.citation,
                "description": "写入文件内容（限制在workspace目录内）",
                "parameters": {
                "type": "object",
                "properties": {
                                "file_path": {
                                                "type": "string",
                                                "description": "文件路径，相对于workspace目录"
                                },
                                "content": {
                                                "type": "string",
                                                "description": "要写入的内容"
                                },
                                "encoding": {
                                                "type": "string",
                                                "description": "文件编码",
                                                "default": "utf-8"
                                }
                },
                "required": [
                                "file_path",
                                "content"
                ]
}
            }
        }


# 实例化工具
write_file_tool = Write_FileTool()
tools = write_file_tool.get_tools()
