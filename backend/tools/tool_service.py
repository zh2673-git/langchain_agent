"""
工具服务 - 提供统一的工具管理接口
Agent通过此服务调用工具，不直接处理工具管理逻辑

支持LangChain的两种工具定义方式：
1. @tool装饰器
2. StructuredTool.from_function

直接基于LangChain实现，无需额外的管理层
"""

import json
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod
from langchain_core.tools import BaseTool, tool, Tool, StructuredTool

try:
    from pydantic import BaseModel
except ImportError:
    from langchain_core.pydantic_v1 import BaseModel

from ..config import config
from ..utils.logger import get_logger

logger = get_logger(__name__)

# 导入统一工具适配器
try:
    from .adapters.universal_tool_adapter import universal_adapter, auto_discovery
    UNIVERSAL_ADAPTER_AVAILABLE = True
    logger.info("Universal tool adapter loaded successfully")
except ImportError as e:
    logger.warning(f"Universal tool adapter not available: {e}")
    UNIVERSAL_ADAPTER_AVAILABLE = False
    universal_adapter = None
    auto_discovery = None


class ToolServiceInterface(ABC):
    """工具服务接口"""
    
    @abstractmethod
    async def initialize(self, llm=None, provider: str = None, model: str = None) -> bool:
        """初始化工具服务"""
        pass
    
    @abstractmethod
    def get_tools(self) -> List[BaseTool]:
        """获取所有可用工具"""
        pass
    
    @abstractmethod
    def get_tools_description(self) -> str:
        """获取工具描述文本"""
        pass
    
    @abstractmethod
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """执行指定工具"""
        pass
    
    @abstractmethod
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具详细信息"""
        pass
    
    @abstractmethod
    def list_tool_names(self) -> List[str]:
        """列出所有工具名称"""
        pass


class ToolService(ToolServiceInterface):
    """
    工具服务实现

    直接基于LangChain实现，提供统一的服务接口
    Agent只需要调用此服务，不需要了解具体的工具管理逻辑
    """

    def __init__(self):
        self.llm = None
        self.provider = None
        self.model = None
        self.supports_native_tools = True

        # 工具存储 - 统一使用LangChain BaseTool接口
        self.tools: Dict[str, BaseTool] = {}
        self._initialized = False

    async def initialize(self, llm=None, provider: str = None, model: str = None) -> bool:
        """初始化工具服务"""
        try:
            self.llm = llm
            self.provider = provider
            self.model = model

            # 检测模型是否支持原生工具调用
            self.supports_native_tools = config.model_supports_tools(provider, model) if provider and model else True

            # 加载所有工具
            await self._load_all_tools()

            self._initialized = True
            logger.info("ToolService initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize ToolService: {e}")
            return False
    
    async def _load_all_tools(self):
        """加载所有工具"""
        try:
            from .tool_loader import get_tool_loader

            # 使用统一工具加载器
            tool_loader = get_tool_loader()
            tools = await tool_loader.load_all_tools()

            # 注册所有工具到统一适配器
            if UNIVERSAL_ADAPTER_AVAILABLE and universal_adapter:
                # 自动发现并注册现有工具
                auto_discovery.discover_and_register_langchain_tools(self)
                # 注册通用工具
                auto_discovery.register_universal_tools()

                # 获取适配器中的LangChain工具
                adapter_tools = universal_adapter.get_langchain_tools()
                tools.extend(adapter_tools)

                logger.info(f"Universal adapter registered {len(adapter_tools)} additional tools")

            # 注册所有工具
            for tool in tools:
                self.add_tool(tool)

            logger.info(f"Loaded {len(tools)} tools from unified loader")
        except Exception as e:
            logger.error(f"Failed to load tools: {e}")
            # 降级到示例工具
            await self._load_example_tools()

    async def _load_example_tools(self):
        """加载示例工具（降级方案）"""
        try:
            from .builtin.example_tools import get_example_tools

            for tool in get_example_tools():
                self.add_tool(tool)

            logger.info("Example tools loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load example tools: {e}")
    
    def get_tools(self) -> List[BaseTool]:
        """获取所有可用工具"""
        if not self._initialized:
            return []
        return list(self.tools.values())

    def get_tools_description(self) -> str:
        """获取工具描述文本"""
        if not self._initialized:
            return "No tools available"

        if not self.tools:
            return "当前没有可用的工具。"

        descriptions = []
        for tool_name, tool_obj in self.tools.items():
            # 获取工具参数信息
            params_info = ""
            if hasattr(tool_obj, 'args_schema') and tool_obj.args_schema:
                try:
                    # 使用新的model_json_schema方法
                    if hasattr(tool_obj.args_schema, 'model_json_schema'):
                        schema = tool_obj.args_schema.model_json_schema()
                    elif hasattr(tool_obj.args_schema, 'schema'):
                        schema = tool_obj.args_schema.schema()
                    else:
                        schema = {}
                    if 'properties' in schema:
                        params_info = f"\n参数: {json.dumps(schema['properties'], ensure_ascii=False, indent=2)}"
                except Exception as e:
                    logger.debug(f"Failed to get schema for tool {tool_name}: {e}")

            description = f"""
**{tool_name}**
描述: {tool_obj.description}{params_info}
"""
            descriptions.append(description)

        return "\n".join(descriptions)

    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """执行指定工具"""
        if not self._initialized:
            return {
                "success": False,
                "error": "Tool service not initialized"
            }

        if tool_name not in self.tools:
            return {
                "success": False,
                "result": f"工具 {tool_name} 不存在"
            }

        try:
            tool_obj = self.tools[tool_name]

            # 使用LangChain标准的run方法执行工具
            if hasattr(tool_obj, 'run'):
                result = tool_obj.run(kwargs)
            elif hasattr(tool_obj, 'func'):
                # 对于Tool类型的工具
                result = tool_obj.func(**kwargs)
            else:
                return {
                    "success": False,
                    "result": f"工具 {tool_name} 没有可执行的方法"
                }

            # 标准化返回格式
            if isinstance(result, dict):
                return result
            else:
                return {
                    "success": True,
                    "result": str(result)
                }

        except Exception as e:
            logger.error(f"Tool {tool_name} execution failed: {e}")
            return {
                "success": False,
                "result": f"工具执行失败: {str(e)}"
            }

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具详细信息"""
        if not self._initialized:
            return None

        if tool_name not in self.tools:
            return None

        tool_obj = self.tools[tool_name]
        info = {
            "name": tool_obj.name,
            "description": tool_obj.description,
            "supports_native": self.supports_native_tools,
            "type": type(tool_obj).__name__
        }

        # 获取参数信息
        if hasattr(tool_obj, 'args_schema') and tool_obj.args_schema:
            try:
                if hasattr(tool_obj.args_schema, 'model_json_schema'):
                    info["parameters"] = tool_obj.args_schema.model_json_schema()
                else:
                    info["parameters"] = {}
            except Exception as e:
                logger.debug(f"Failed to get parameters for tool {tool_name}: {e}")
                info["parameters"] = {}
        else:
            info["parameters"] = {}

        return info

    def list_tool_names(self) -> List[str]:
        """列出所有工具名称"""
        if not self._initialized:
            return []
        return list(self.tools.keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """获取工具服务统计信息"""
        return {
            "initialized": self._initialized,
            "total_tools": len(self.tools),
            "supports_native_tools": self.supports_native_tools,
            "provider": self.provider,
            "model": self.model,
            "tool_names": list(self.tools.keys()),
            "tool_types": [type(tool).__name__ for tool in self.tools.values()]
        }

    # 工具管理方法
    def add_tool(self, tool: BaseTool) -> bool:
        """添加工具"""
        try:
            if not isinstance(tool, BaseTool):
                raise ValueError(f"Tool must be an instance of BaseTool, got {type(tool)}")

            self.tools[tool.name] = tool
            logger.info(f"Added tool: {tool.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add tool: {e}")
            return False

    def add_function_as_tool(self, func: Callable, name: str = None,
                           description: str = None, args_schema: BaseModel = None) -> bool:
        """将普通函数转换为LangChain工具"""
        try:
            tool_name = name or func.__name__
            tool_description = description or func.__doc__ or f"Tool: {tool_name}"

            if args_schema:
                # 使用StructuredTool.from_function创建复杂工具
                tool_obj = StructuredTool.from_function(
                    func=func,
                    name=tool_name,
                    description=tool_description,
                    args_schema=args_schema
                )
            else:
                # 使用简单的Tool包装
                tool_obj = Tool(
                    name=tool_name,
                    description=tool_description,
                    func=func
                )

            return self.add_tool(tool_obj)
        except Exception as e:
            logger.error(f"Failed to add function as tool: {e}")
            return False

    def create_tool_from_decorator(self, func: Callable) -> Optional[BaseTool]:
        """使用@tool装饰器创建工具"""
        try:
            # 使用@tool装饰器
            tool_obj = tool(func)
            if self.add_tool(tool_obj):
                return tool_obj
            return None
        except Exception as e:
            logger.error(f"Failed to create tool from decorator: {e}")
            return None

    def remove_tool(self, tool_name: str) -> bool:
        """移除工具"""
        try:
            if tool_name not in self.tools:
                return False

            del self.tools[tool_name]
            logger.info(f"Removed tool: {tool_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove tool: {e}")
            return False

    def clear_tools(self):
        """清空所有工具"""
        self.tools.clear()
        logger.info("Cleared all tools")

    def get_openwebui_tools(self) -> Dict[str, Dict]:
        """获取OpenWebUI格式的工具"""
        if UNIVERSAL_ADAPTER_AVAILABLE and universal_adapter:
            return universal_adapter.get_openwebui_tools()
        return {}

    def register_universal_tool(self, name: str, function: Callable, description: str,
                               parameters: Optional[Dict[str, Any]] = None) -> bool:
        """注册统一工具（同时生成LangChain和OpenWebUI格式）"""
        try:
            if UNIVERSAL_ADAPTER_AVAILABLE and universal_adapter:
                universal_adapter.register_tool(
                    name=name,
                    function=function,
                    description=description,
                    parameters=parameters
                )

                # 获取生成的LangChain工具并添加到服务中
                langchain_tools = universal_adapter.get_langchain_tools()
                for tool in langchain_tools:
                    if tool.name == name:
                        self.add_tool(tool)
                        break

                logger.info(f"Registered universal tool: {name}")
                return True
            else:
                logger.warning("Universal adapter not available")
                return False

        except Exception as e:
            logger.error(f"Failed to register universal tool {name}: {e}")
            return False

    def list_tool_names(self) -> List[str]:
        """列出所有工具名称"""
        return list(self.tools.keys())


# 全局工具服务实例
_tool_service_instance: Optional[ToolService] = None


def get_tool_service() -> ToolService:
    """获取全局工具服务实例"""
    global _tool_service_instance
    if _tool_service_instance is None:
        _tool_service_instance = ToolService()
    return _tool_service_instance


async def initialize_tool_service(llm=None, provider: str = None, model: str = None) -> bool:
    """初始化全局工具服务"""
    service = get_tool_service()
    return await service.initialize(llm, provider, model)
