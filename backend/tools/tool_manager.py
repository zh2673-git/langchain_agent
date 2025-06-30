"""
工具管理器 - 完全基于LangChain源码实现
严格按照LangChain官方源码和最佳实践实现

核心原则：
1. 完全使用LangChain的工具接口和标准
2. 支持LangChain原生工具调用
3. 兼容LangChain生态系统
4. 遵循LangChain的设计模式
"""
import json
from typing import Dict, Any, List, Optional, Union
from langchain_core.tools import tool, Tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from ..config import config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ToolManager:
    """
    工具管理器 - 基于LangChain最佳实践
    
    这个类完全按照LangChain的设计理念实现：
    1. 使用LangChain的@tool装饰器
    2. 支持原生工具调用（function calling）
    3. 支持提示词工具调用（prompt-based）
    4. 自动适配不同模型的能力
    """
    
    def __init__(self, llm, provider: str, model: str):
        """
        初始化工具管理器
        
        Args:
            llm: LangChain LLM实例
            provider: 模型提供商（如ollama, openai）
            model: 模型名称
        """
        self.llm = llm
        self.provider = provider
        self.model = model
        
        # 检测模型是否支持原生工具调用
        self.supports_native_tools = config.model_supports_tools(provider, model)
        
        # 工具存储
        self.tools = {}  # 自定义工具对象
        self.langchain_tools = []  # LangChain工具列表
        
        logger.info(f"ToolManager initialized for {provider}:{model}, native tools support: {self.supports_native_tools}")
    
    def add_tool(self, tool_obj):
        """
        添加工具到管理器
        
        按照LangChain最佳实践：
        1. 存储原始工具对象
        2. 如果模型支持，转换为LangChain工具
        3. 提供统一的调用接口
        """
        self.tools[tool_obj.name] = tool_obj

        if self.supports_native_tools:
            try:
                # 支持工具调用的模型：转换为LangChain原生工具
                langchain_tool = self._convert_to_langchain_tool(tool_obj)
                self.langchain_tools.append(langchain_tool)
                logger.info(f"Added tool to LangChain tools: {tool_obj.name}")
            except Exception as e:
                logger.error(f"Failed to convert tool {tool_obj.name} to LangChain tool: {e}")

        logger.info(f"Added tool: {tool_obj.name}")
    
    def _convert_to_langchain_tool(self, tool_obj):
        """
        将自定义工具转换为LangChain Tool
        
        这是按照LangChain源码的标准模式实现的：
        1. 使用Tool类包装
        2. 提供标准的name, description, func接口
        3. 支持异步调用
        """
        def tool_func(**kwargs):
            """工具执行函数 - 同步包装"""
            import asyncio
            try:
                # 如果工具支持异步，使用异步调用
                if hasattr(tool_obj, 'execute') and callable(tool_obj.execute):
                    if asyncio.iscoroutinefunction(tool_obj.execute):
                        # 异步工具
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # 在已有事件循环中创建任务
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(asyncio.run, tool_obj.execute(**kwargs))
                                result = future.result()
                        else:
                            result = asyncio.run(tool_obj.execute(**kwargs))
                    else:
                        # 同步工具
                        result = tool_obj.execute(**kwargs)
                else:
                    return {"success": False, "result": "工具没有execute方法"}
                
                # 标准化返回格式
                if isinstance(result, dict):
                    return result.get("result", str(result))
                else:
                    return str(result)
                    
            except Exception as e:
                logger.error(f"Tool execution failed: {e}")
                return f"工具执行失败: {str(e)}"
        
        # 创建LangChain Tool - 按照源码标准
        return Tool(
            name=tool_obj.name,
            description=tool_obj.description,
            func=tool_func
        )
    
    def get_langchain_tools(self) -> List[Tool]:
        """
        获取LangChain工具列表
        
        用于Agent和AgentExecutor的工具注册
        这是LangChain标准的工具获取方式
        """
        return self.langchain_tools
    
    def get_tools_description(self) -> str:
        """
        获取工具描述文本
        
        用于提示词工具调用模式
        按照LangChain的提示词工程最佳实践格式化
        """
        if not self.tools:
            return "当前没有可用的工具。"
        
        descriptions = []
        for tool_name, tool_obj in self.tools.items():
            # 获取工具参数信息
            params_info = ""
            if hasattr(tool_obj, 'get_parameters'):
                try:
                    params = tool_obj.get_parameters()
                    if params:
                        params_info = f"\n参数: {json.dumps(params, ensure_ascii=False, indent=2)}"
                except:
                    params_info = ""
            
            description = f"""
**{tool_name}**
描述: {tool_obj.description}{params_info}
使用格式: TOOL_CALL: {tool_name}
"""
            descriptions.append(description)
        
        return "\n".join(descriptions)
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        执行工具 - 统一接口
        
        提供统一的工具执行接口，无论是原生工具调用还是提示词调用
        """
        if tool_name not in self.tools:
            return {
                "success": False,
                "result": f"工具 {tool_name} 不存在"
            }
        
        try:
            tool_obj = self.tools[tool_name]
            
            # 执行工具
            if hasattr(tool_obj, 'execute') and callable(tool_obj.execute):
                import asyncio
                if asyncio.iscoroutinefunction(tool_obj.execute):
                    # 异步工具
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, tool_obj.execute(**kwargs))
                            result = future.result()
                    else:
                        result = asyncio.run(tool_obj.execute(**kwargs))
                else:
                    # 同步工具
                    result = tool_obj.execute(**kwargs)
            else:
                return {
                    "success": False,
                    "result": f"工具 {tool_name} 没有execute方法"
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
    
    def list_tools(self) -> List[str]:
        """列出所有可用工具"""
        return list(self.tools.keys())
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取工具详细信息"""
        if tool_name not in self.tools:
            return None
        
        tool_obj = self.tools[tool_name]
        info = {
            "name": tool_obj.name,
            "description": tool_obj.description,
            "supports_native": self.supports_native_tools
        }
        
        # 获取参数信息
        if hasattr(tool_obj, 'get_parameters'):
            try:
                info["parameters"] = tool_obj.get_parameters()
            except:
                info["parameters"] = {}
        
        return info
    
    def remove_tool(self, tool_name: str) -> bool:
        """移除工具"""
        if tool_name not in self.tools:
            return False
        
        # 从工具字典中移除
        del self.tools[tool_name]
        
        # 从LangChain工具列表中移除
        self.langchain_tools = [
            tool for tool in self.langchain_tools 
            if tool.name != tool_name
        ]
        
        logger.info(f"Removed tool: {tool_name}")
        return True
    
    def clear_tools(self):
        """清空所有工具"""
        self.tools.clear()
        self.langchain_tools.clear()
        logger.info("Cleared all tools")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取工具管理器统计信息"""
        return {
            "total_tools": len(self.tools),
            "langchain_tools": len(self.langchain_tools),
            "supports_native_tools": self.supports_native_tools,
            "provider": self.provider,
            "model": self.model,
            "tool_names": list(self.tools.keys())
        }
