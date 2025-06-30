"""
LangChain工具转换器
将自定义工具转换为LangChain标准工具
完全基于LangChain源码实现
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Type
from langchain_core.tools import BaseTool, tool
from langchain_core.pydantic_v1 import BaseModel, Field

from ..utils.logger import get_logger

logger = get_logger(__name__)


class LangChainToolConverter:
    """
    LangChain工具转换器
    
    将自定义工具转换为LangChain标准工具
    完全按照LangChain源码标准实现
    """
    
    @staticmethod
    def convert_to_langchain_tool(custom_tool) -> BaseTool:
        """
        将自定义工具转换为LangChain工具
        
        Args:
            custom_tool: 自定义工具对象
            
        Returns:
            BaseTool: LangChain标准工具
        """
        try:
            # 如果工具已经有to_langchain_tool方法，直接使用
            if hasattr(custom_tool, 'to_langchain_tool'):
                return custom_tool.to_langchain_tool()
            
            # 否则创建包装器
            return LangChainToolConverter._create_tool_wrapper(custom_tool)
            
        except Exception as e:
            logger.error(f"Failed to convert tool {custom_tool.name}: {e}")
            # 返回一个简单的错误工具
            return LangChainToolConverter._create_error_tool(custom_tool.name, str(e))
    
    @staticmethod
    def _create_tool_wrapper(custom_tool) -> BaseTool:
        """创建工具包装器"""
        
        # 创建输入模型
        input_model = LangChainToolConverter._create_input_model(custom_tool)
        
        class WrappedTool(BaseTool):
            name: str = custom_tool.name
            description: str = custom_tool.description
            args_schema: Type[BaseModel] = input_model
            
            def _run(self, **kwargs) -> str:
                """同步执行工具"""
                try:
                    # 执行自定义工具
                    if hasattr(custom_tool, 'execute'):
                        if asyncio.iscoroutinefunction(custom_tool.execute):
                            # 异步工具需要在事件循环中执行
                            try:
                                loop = asyncio.get_event_loop()
                                if loop.is_running():
                                    # 在已有事件循环中创建任务
                                    import concurrent.futures
                                    with concurrent.futures.ThreadPoolExecutor() as executor:
                                        future = executor.submit(asyncio.run, custom_tool.execute(**kwargs))
                                        result = future.result()
                                else:
                                    result = asyncio.run(custom_tool.execute(**kwargs))
                            except Exception as e:
                                logger.error(f"Async tool execution failed: {e}")
                                result = {"success": False, "result": f"异步执行失败: {str(e)}"}
                        else:
                            # 同步工具直接执行
                            result = custom_tool.execute(**kwargs)
                    else:
                        return f"工具 {custom_tool.name} 没有execute方法"
                    
                    # 格式化返回结果
                    if isinstance(result, dict):
                        if result.get("success", True):
                            return str(result.get("result", result))
                        else:
                            return f"工具执行失败: {result.get('result', result)}"
                    else:
                        return str(result)
                        
                except Exception as e:
                    logger.error(f"Tool execution failed: {e}")
                    return f"工具执行失败: {str(e)}"
            
            async def _arun(self, **kwargs) -> str:
                """异步执行工具"""
                try:
                    if hasattr(custom_tool, 'execute'):
                        if asyncio.iscoroutinefunction(custom_tool.execute):
                            result = await custom_tool.execute(**kwargs)
                        else:
                            result = custom_tool.execute(**kwargs)
                    else:
                        return f"工具 {custom_tool.name} 没有execute方法"
                    
                    # 格式化返回结果
                    if isinstance(result, dict):
                        if result.get("success", True):
                            return str(result.get("result", result))
                        else:
                            return f"工具执行失败: {result.get('result', result)}"
                    else:
                        return str(result)
                        
                except Exception as e:
                    logger.error(f"Async tool execution failed: {e}")
                    return f"异步工具执行失败: {str(e)}"
        
        return WrappedTool()
    
    @staticmethod
    def _create_input_model(custom_tool) -> Type[BaseModel]:
        """创建输入模型"""
        
        # 获取工具参数
        parameters = {}
        if hasattr(custom_tool, 'get_parameters'):
            try:
                params = custom_tool.get_parameters()
                if params:
                    parameters = params
            except Exception as e:
                logger.warning(f"Failed to get parameters for tool {custom_tool.name}: {e}")
        
        # 创建字段
        fields = {}
        
        if parameters:
            for param_name, param_info in parameters.items():
                if isinstance(param_info, dict):
                    param_type = param_info.get('type', 'string')
                    param_desc = param_info.get('description', f'{param_name} parameter')
                    param_required = param_info.get('required', False)
                    param_default = param_info.get('default')
                    
                    # 映射类型
                    if param_type == 'string':
                        field_type = str
                    elif param_type == 'number':
                        field_type = float
                    elif param_type == 'integer':
                        field_type = int
                    elif param_type == 'boolean':
                        field_type = bool
                    else:
                        field_type = str
                    
                    # 创建字段
                    if param_required:
                        fields[param_name] = (field_type, Field(description=param_desc))
                    else:
                        if param_default is not None:
                            fields[param_name] = (field_type, Field(default=param_default, description=param_desc))
                        else:
                            fields[param_name] = (Optional[field_type], Field(default=None, description=param_desc))
        
        # 如果没有参数，创建一个通用的输入字段
        if not fields:
            fields['input'] = (Optional[str], Field(default=None, description="工具输入"))
        
        # 动态创建模型类
        model_name = f"{custom_tool.name.title()}Input"
        input_model = type(model_name, (BaseModel,), fields)
        
        return input_model
    
    @staticmethod
    def _create_error_tool(tool_name: str, error_msg: str) -> BaseTool:
        """创建错误工具"""
        
        class ErrorInput(BaseModel):
            input: Optional[str] = Field(default=None, description="输入")
        
        class ErrorTool(BaseTool):
            name: str = tool_name
            description: str = f"错误工具: {error_msg}"
            args_schema: Type[BaseModel] = ErrorInput
            
            def _run(self, **kwargs) -> str:
                return f"工具 {tool_name} 转换失败: {error_msg}"
            
            async def _arun(self, **kwargs) -> str:
                return f"工具 {tool_name} 转换失败: {error_msg}"
        
        return ErrorTool()
    
    @staticmethod
    def convert_tools_list(custom_tools: List) -> List[BaseTool]:
        """
        批量转换工具列表
        
        Args:
            custom_tools: 自定义工具列表
            
        Returns:
            List[BaseTool]: LangChain工具列表
        """
        langchain_tools = []
        
        for custom_tool in custom_tools:
            try:
                langchain_tool = LangChainToolConverter.convert_to_langchain_tool(custom_tool)
                langchain_tools.append(langchain_tool)
                logger.info(f"Successfully converted tool: {custom_tool.name}")
            except Exception as e:
                logger.error(f"Failed to convert tool {custom_tool.name}: {e}")
                # 添加错误工具
                error_tool = LangChainToolConverter._create_error_tool(custom_tool.name, str(e))
                langchain_tools.append(error_tool)
        
        return langchain_tools
    
    @staticmethod
    def validate_langchain_tool(tool: BaseTool) -> bool:
        """
        验证LangChain工具是否有效
        
        Args:
            tool: LangChain工具
            
        Returns:
            bool: 是否有效
        """
        try:
            # 检查必要属性
            if not hasattr(tool, 'name') or not tool.name:
                return False
            
            if not hasattr(tool, 'description') or not tool.description:
                return False
            
            if not hasattr(tool, '_run') and not hasattr(tool, '_arun'):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Tool validation failed: {e}")
            return False
