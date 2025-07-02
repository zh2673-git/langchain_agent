"""
统一工具适配器
实现LangChain工具和OpenWebUI工具的双向转换和无缝集成
"""

import inspect
import json
from typing import Any, Dict, List, Callable, Optional, Union
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, tool
from langchain_core.tools.structured import StructuredTool
import logging

logger = logging.getLogger(__name__)


class UniversalToolDefinition(BaseModel):
    """统一工具定义格式"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    function: Callable = Field(..., description="工具函数")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="参数定义")
    return_direct: bool = Field(default=False, description="是否直接返回结果")
    citation: bool = Field(default=True, description="是否需要引用")


class UniversalToolAdapter:
    """统一工具适配器"""
    
    def __init__(self):
        self.tools_registry: Dict[str, UniversalToolDefinition] = {}
        self.langchain_tools: Dict[str, BaseTool] = {}
        self.openwebui_tools: Dict[str, Dict] = {}
    
    def register_tool(self, 
                     name: str,
                     function: Callable,
                     description: str,
                     parameters: Optional[Dict[str, Any]] = None,
                     return_direct: bool = False,
                     citation: bool = True) -> None:
        """
        注册统一工具
        
        Args:
            name: 工具名称
            function: 工具函数
            description: 工具描述
            parameters: 参数定义（JSON Schema格式）
            return_direct: 是否直接返回结果
            citation: 是否需要引用
        """
        # 如果没有提供参数定义，尝试从函数签名自动生成
        if parameters is None:
            parameters = self._extract_parameters_from_function(function)
        
        tool_def = UniversalToolDefinition(
            name=name,
            description=description,
            function=function,
            parameters=parameters,
            return_direct=return_direct,
            citation=citation
        )
        
        self.tools_registry[name] = tool_def
        
        # 自动生成LangChain和OpenWebUI格式
        self._generate_langchain_tool(tool_def)
        self._generate_openwebui_tool(tool_def)
        
        logger.info(f"Registered universal tool: {name}")
    
    def _extract_parameters_from_function(self, func: Callable) -> Dict[str, Any]:
        """从函数签名自动提取参数定义"""
        try:
            sig = inspect.signature(func)
            parameters = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            for param_name, param in sig.parameters.items():
                param_info = {"type": "string"}  # 默认类型
                
                # 尝试从类型注解获取类型
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == int:
                        param_info["type"] = "integer"
                    elif param.annotation == float:
                        param_info["type"] = "number"
                    elif param.annotation == bool:
                        param_info["type"] = "boolean"
                    elif param.annotation == list:
                        param_info["type"] = "array"
                    elif param.annotation == dict:
                        param_info["type"] = "object"
                
                # 处理默认值
                if param.default != inspect.Parameter.empty:
                    param_info["default"] = param.default
                else:
                    parameters["required"].append(param_name)
                
                # 尝试从docstring获取描述
                if func.__doc__:
                    param_info["description"] = f"参数: {param_name}"
                
                parameters["properties"][param_name] = param_info
            
            return parameters
            
        except Exception as e:
            logger.warning(f"Failed to extract parameters from function {func.__name__}: {e}")
            return {
                "type": "object",
                "properties": {},
                "required": []
            }
    
    def _generate_langchain_tool(self, tool_def: UniversalToolDefinition) -> None:
        """生成LangChain工具"""
        try:
            # 使用StructuredTool.from_function创建LangChain工具
            langchain_tool = StructuredTool.from_function(
                func=tool_def.function,
                name=tool_def.name,
                description=tool_def.description,
                return_direct=tool_def.return_direct
            )
            
            self.langchain_tools[tool_def.name] = langchain_tool
            logger.debug(f"Generated LangChain tool: {tool_def.name}")
            
        except Exception as e:
            logger.error(f"Failed to generate LangChain tool {tool_def.name}: {e}")
    
    def _generate_openwebui_tool(self, tool_def: UniversalToolDefinition) -> None:
        """生成OpenWebUI工具"""
        try:
            openwebui_tool = {
                "callable": tool_def.function,
                "citation": tool_def.citation,
                "description": tool_def.description,
                "parameters": tool_def.parameters
            }
            
            self.openwebui_tools[tool_def.name] = openwebui_tool
            logger.debug(f"Generated OpenWebUI tool: {tool_def.name}")
            
        except Exception as e:
            logger.error(f"Failed to generate OpenWebUI tool {tool_def.name}: {e}")
    
    def import_langchain_tool(self, langchain_tool: BaseTool) -> None:
        """导入现有的LangChain工具"""
        try:
            name = langchain_tool.name
            description = langchain_tool.description
            
            # 提取函数
            if hasattr(langchain_tool, '_run'):
                function = langchain_tool._run
            elif hasattr(langchain_tool, 'func'):
                function = langchain_tool.func
            else:
                # 创建包装函数
                def wrapper(*args, **kwargs):
                    return langchain_tool.run(*args, **kwargs)
                function = wrapper
            
            # 提取参数定义
            parameters = {}
            if hasattr(langchain_tool, 'args_schema') and langchain_tool.args_schema:
                # 从Pydantic模型提取参数
                parameters = self._pydantic_to_json_schema(langchain_tool.args_schema)
            else:
                # 从函数签名提取
                parameters = self._extract_parameters_from_function(function)
            
            # 注册为统一工具
            self.register_tool(
                name=name,
                function=function,
                description=description,
                parameters=parameters,
                return_direct=getattr(langchain_tool, 'return_direct', False)
            )
            
            logger.info(f"Imported LangChain tool: {name}")
            
        except Exception as e:
            logger.error(f"Failed to import LangChain tool {langchain_tool.name}: {e}")
    
    def _pydantic_to_json_schema(self, pydantic_model) -> Dict[str, Any]:
        """将Pydantic模型转换为JSON Schema"""
        try:
            if hasattr(pydantic_model, 'model_json_schema'):
                # Pydantic v2
                return pydantic_model.model_json_schema()
            elif hasattr(pydantic_model, 'schema'):
                # Pydantic v1
                return pydantic_model.schema()
            else:
                return {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
        except Exception as e:
            logger.warning(f"Failed to convert Pydantic model to JSON schema: {e}")
            return {
                "type": "object",
                "properties": {},
                "required": []
            }
    
    def get_langchain_tools(self) -> List[BaseTool]:
        """获取所有LangChain格式的工具"""
        return list(self.langchain_tools.values())
    
    def get_openwebui_tools(self) -> Dict[str, Dict]:
        """获取所有OpenWebUI格式的工具"""
        return self.openwebui_tools.copy()
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具信息"""
        if tool_name in self.tools_registry:
            tool_def = self.tools_registry[tool_name]
            return {
                "name": tool_def.name,
                "description": tool_def.description,
                "parameters": tool_def.parameters,
                "return_direct": tool_def.return_direct,
                "citation": tool_def.citation
            }
        return None
    
    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self.tools_registry.keys())
    
    def remove_tool(self, tool_name: str) -> bool:
        """移除工具"""
        if tool_name in self.tools_registry:
            del self.tools_registry[tool_name]
            if tool_name in self.langchain_tools:
                del self.langchain_tools[tool_name]
            if tool_name in self.openwebui_tools:
                del self.openwebui_tools[tool_name]
            logger.info(f"Removed tool: {tool_name}")
            return True
        return False


# 全局适配器实例
universal_adapter = UniversalToolAdapter()


class ToolAutoDiscovery:
    """工具自动发现和注册系统"""

    def __init__(self, adapter: UniversalToolAdapter):
        self.adapter = adapter

    def discover_and_register_langchain_tools(self, tool_service) -> None:
        """自动发现并注册现有的LangChain工具"""
        try:
            # 获取所有LangChain工具
            if hasattr(tool_service, 'builtin_tools'):
                for tool in tool_service.builtin_tools:
                    self.adapter.import_langchain_tool(tool)

            if hasattr(tool_service, 'custom_tools'):
                for tool in tool_service.custom_tools:
                    self.adapter.import_langchain_tool(tool)

            if hasattr(tool_service, 'mcp_tools'):
                for tool in tool_service.mcp_tools:
                    self.adapter.import_langchain_tool(tool)

            logger.info("Completed LangChain tools discovery and registration")

        except Exception as e:
            logger.error(f"Failed to discover LangChain tools: {e}")

    def register_universal_tools(self) -> None:
        """注册通用工具定义"""
        # 这里可以注册一些通用的工具定义
        self._register_calculator()
        self._register_datetime_tool()
        self._register_web_search()

    def _register_calculator(self):
        """注册计算器工具"""
        def calculate(expression: str) -> str:
            """
            计算数学表达式

            Args:
                expression: 要计算的数学表达式，例如 "2 + 3 * 4"

            Returns:
                计算结果
            """
            import ast
            import operator

            try:
                # 安全的数学运算符
                operators = {
                    ast.Add: operator.add,
                    ast.Sub: operator.sub,
                    ast.Mult: operator.mul,
                    ast.Div: operator.truediv,
                    ast.Pow: operator.pow,
                    ast.USub: operator.neg,
                    ast.UAdd: operator.pos,
                    ast.Mod: operator.mod,
                }

                def eval_expr(node):
                    if isinstance(node, ast.Constant):
                        return node.value
                    elif isinstance(node, ast.Num):
                        return node.n
                    elif isinstance(node, ast.BinOp):
                        return operators[type(node.op)](eval_expr(node.left), eval_expr(node.right))
                    elif isinstance(node, ast.UnaryOp):
                        return operators[type(node.op)](eval_expr(node.operand))
                    else:
                        raise TypeError(f"不支持的操作: {type(node)}")

                tree = ast.parse(expression, mode='eval')
                result = eval_expr(tree.body)
                return f"计算结果: {result}"

            except Exception as e:
                return f"计算错误: {str(e)}"

        self.adapter.register_tool(
            name="calculate",
            function=calculate,
            description="计算数学表达式，支持基本的四则运算、幂运算和取模运算",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式，例如 '2 + 3 * 4'"
                    }
                },
                "required": ["expression"]
            }
        )

    def _register_datetime_tool(self):
        """注册时间工具"""
        def get_current_time(timezone_name: str = "Asia/Shanghai") -> str:
            """
            获取当前时间

            Args:
                timezone_name: 时区名称，默认为Asia/Shanghai

            Returns:
                当前时间信息
            """
            from datetime import datetime
            import pytz

            try:
                tz = pytz.timezone(timezone_name)
                current_time = datetime.now(tz)
                formatted_time = current_time.strftime("%Y年%m月%d日 %H:%M:%S")
                weekday = current_time.strftime("%A")

                weekday_map = {
                    "Monday": "星期一", "Tuesday": "星期二", "Wednesday": "星期三",
                    "Thursday": "星期四", "Friday": "星期五", "Saturday": "星期六", "Sunday": "星期日"
                }

                chinese_weekday = weekday_map.get(weekday, weekday)
                return f"当前时间: {formatted_time} {chinese_weekday} (时区: {timezone_name})"

            except Exception as e:
                return f"获取时间失败: {str(e)}"

        self.adapter.register_tool(
            name="get_current_time",
            function=get_current_time,
            description="获取当前日期和时间，支持不同时区",
            parameters={
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
        )

    def _register_web_search(self):
        """注册网络搜索工具"""
        def web_search(query: str, num_results: int = 5) -> str:
            """
            搜索网络信息

            Args:
                query: 搜索查询
                num_results: 返回结果数量

            Returns:
                搜索结果
            """
            import requests
            from urllib.parse import quote

            try:
                url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1&skip_disambig=1"
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                data = response.json()
                results = []

                if data.get('Answer'):
                    results.append(f"答案: {data['Answer']}")

                if data.get('Abstract'):
                    results.append(f"摘要: {data['Abstract']}")

                if data.get('RelatedTopics'):
                    for i, topic in enumerate(data['RelatedTopics'][:num_results]):
                        if isinstance(topic, dict) and 'Text' in topic:
                            results.append(f"相关 {i+1}: {topic['Text']}")

                return "\n".join(results[:num_results]) if results else "未找到相关信息"

            except Exception as e:
                return f"搜索失败: {str(e)}"

        self.adapter.register_tool(
            name="web_search",
            function=web_search,
            description="搜索网络信息，获取实时数据和答案",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "返回结果数量，默认5个",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["query"]
            }
        )


# 全局自动发现实例
auto_discovery = ToolAutoDiscovery(universal_adapter)
