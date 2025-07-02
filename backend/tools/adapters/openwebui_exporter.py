"""
OpenWebUI工具导出器
将统一适配器中的工具导出为OpenWebUI可用的格式
"""

import os
import json
from typing import Dict, Any
from .universal_tool_adapter import universal_adapter
from ...utils.logger import get_logger

logger = get_logger(__name__)


class OpenWebUIExporter:
    """OpenWebUI工具导出器"""
    
    def __init__(self, export_path: str = None):
        if export_path is None:
            # 自动检测正确的导出路径
            current_dir = os.getcwd()
            if current_dir.endswith('docker'):
                self.export_path = "openwebui_tools"
            else:
                self.export_path = "docker/openwebui_tools"
        else:
            self.export_path = export_path
        self.ensure_export_directory()
    
    def ensure_export_directory(self):
        """确保导出目录存在"""
        try:
            os.makedirs(self.export_path, exist_ok=True)
            logger.info(f"Export directory ensured: {self.export_path}")
        except Exception as e:
            logger.error(f"Failed to create export directory: {e}")
    
    def export_all_tools(self) -> bool:
        """导出所有工具为OpenWebUI格式"""
        try:
            openwebui_tools = universal_adapter.get_openwebui_tools()
            
            if not openwebui_tools:
                logger.warning("No tools to export")
                return True
            
            # 为每个工具创建单独的文件
            for tool_name, tool_config in openwebui_tools.items():
                self._export_single_tool(tool_name, tool_config)
            
            # 创建工具索引文件
            self._create_tools_index(openwebui_tools)
            
            logger.info(f"Exported {len(openwebui_tools)} tools to OpenWebUI format")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export tools: {e}")
            return False
    
    def _export_single_tool(self, tool_name: str, tool_config: Dict[str, Any]):
        """导出单个工具"""
        try:
            # 生成OpenWebUI工具文件内容
            tool_content = self._generate_tool_file_content(tool_name, tool_config)
            
            # 写入文件
            file_path = os.path.join(self.export_path, f"{tool_name}.py")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(tool_content)
            
            logger.debug(f"Exported tool: {tool_name} -> {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to export tool {tool_name}: {e}")
    
    def _generate_tool_file_content(self, tool_name: str, tool_config: Dict[str, Any]) -> str:
        """生成OpenWebUI工具文件内容"""
        description = tool_config.get("description", "")
        parameters = tool_config.get("parameters", {})
        citation = tool_config.get("citation", True)
        
        # 生成参数文档
        param_docs = self._generate_parameter_docs(parameters)
        
        content = f'''"""
OpenWebUI工具: {tool_name}
{description}

自动生成的工具文件 - 请勿手动修改
"""

from typing import Any, Dict
import json


class Tools:
    def __init__(self):
        self.citation = {str(citation).lower()}

    def {tool_name}(self{param_docs["signature"]}) -> str:
        """
        {description}
        
{param_docs["docstring"]}
        """
        try:
            # 调用LangChain后端API
            import requests
            
            url = "http://langchain-backend:8000/v1/tools/execute"
            payload = {{
                "tool_name": "{tool_name}",
                "parameters": {{{param_docs["payload"]}}}
            }}
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("result", "执行成功")
            else:
                return f"工具执行失败: {{response.status_code}}"
                
        except Exception as e:
            return f"工具执行错误: {{str(e)}}"


# OpenWebUI工具规范
class {tool_name.title()}Tool:
    """
    OpenWebUI {tool_name} 工具
    """
    
    def __init__(self):
        self.tools = Tools()
    
    def get_tools(self):
        """返回工具定义"""
        return {{
            "{tool_name}": {{
                "callable": self.tools.{tool_name},
                "citation": self.tools.citation,
                "description": "{description}",
                "parameters": {json.dumps(parameters, indent=16, ensure_ascii=False)}
            }}
        }}


# 实例化工具
{tool_name}_tool = {tool_name.title()}Tool()
tools = {tool_name}_tool.get_tools()
'''
        
        return content
    
    def _generate_parameter_docs(self, parameters: Dict[str, Any]) -> Dict[str, str]:
        """生成参数文档"""
        properties = parameters.get("properties", {})
        required = parameters.get("required", [])
        
        # 生成函数签名
        signature_parts = []
        docstring_parts = []
        payload_parts = []
        
        for param_name, param_info in properties.items():
            param_type = param_info.get("type", "str")
            param_desc = param_info.get("description", "")
            default_value = param_info.get("default")
            
            # 类型映射
            type_map = {
                "string": "str",
                "integer": "int", 
                "number": "float",
                "boolean": "bool",
                "array": "list",
                "object": "dict"
            }
            python_type = type_map.get(param_type, "str")
            
            # 函数签名
            if param_name in required:
                signature_parts.append(f", {param_name}: {python_type}")
            else:
                default_str = f'"{default_value}"' if isinstance(default_value, str) else str(default_value)
                if default_value is None:
                    default_str = "None"
                signature_parts.append(f", {param_name}: {python_type} = {default_str}")
            
            # 文档字符串
            docstring_parts.append(f"        :param {param_name}: {param_desc}")
            
            # 载荷参数
            payload_parts.append(f'"{param_name}": {param_name}')
        
        return {
            "signature": "".join(signature_parts),
            "docstring": "\n".join(docstring_parts),
            "payload": ", ".join(payload_parts)
        }
    
    def _create_tools_index(self, tools: Dict[str, Any]):
        """创建工具索引文件"""
        try:
            index_content = f'''"""
OpenWebUI工具索引
自动生成的索引文件 - 请勿手动修改

包含 {len(tools)} 个工具:
{chr(10).join(f"- {name}: {config.get('description', '')}" for name, config in tools.items())}
"""

# 工具列表
AVAILABLE_TOOLS = {json.dumps(list(tools.keys()), indent=4, ensure_ascii=False)}

# 工具描述
TOOL_DESCRIPTIONS = {{
{chr(10).join(f'    "{name}": "{config.get("description", "")}",' for name, config in tools.items())}
}}
'''
            
            index_path = os.path.join(self.export_path, "__init__.py")
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(index_content)
            
            logger.debug(f"Created tools index: {index_path}")
            
        except Exception as e:
            logger.error(f"Failed to create tools index: {e}")


# 全局导出器实例
openwebui_exporter = OpenWebUIExporter()


def export_tools_to_openwebui() -> bool:
    """导出工具到OpenWebUI"""
    return openwebui_exporter.export_all_tools()
