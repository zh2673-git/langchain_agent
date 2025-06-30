"""
工具基类定义
定义工具调用的通用接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class ToolType(str, Enum):
    """工具类型枚举"""
    SEARCH = "search"
    CALCULATOR = "calculator"
    FILE = "file"
    API = "api"
    CUSTOM = "custom"


class ToolParameter(BaseModel):
    """工具参数定义"""
    name: str
    type: str  # string, number, boolean, array, object
    description: str
    required: bool = False
    default: Any = None
    enum: Optional[List[Any]] = None


class ToolSchema(BaseModel):
    """工具模式定义"""
    name: str
    description: str
    parameters: List[ToolParameter] = []
    tool_type: ToolType = ToolType.CUSTOM
    version: str = "1.0.0"
    author: Optional[str] = None


class ToolResult(BaseModel):
    """工具执行结果"""
    success: bool
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}
    execution_time: Optional[float] = None


class ToolBase(ABC):
    """工具基类"""
    
    def __init__(self, name: str, description: str, tool_type: ToolType = ToolType.CUSTOM):
        """
        初始化工具
        
        Args:
            name: 工具名称
            description: 工具描述
            tool_type: 工具类型
        """
        self.name = name
        self.description = description
        self.tool_type = tool_type
        self._schema = None
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化工具
        
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            ToolResult: 执行结果
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> ToolSchema:
        """
        获取工具模式
        
        Returns:
            ToolSchema: 工具模式
        """
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        验证参数
        
        Args:
            parameters: 参数字典
            
        Returns:
            bool: 验证是否通过
        """
        schema = self.get_schema()
        
        # 检查必需参数
        for param in schema.parameters:
            if param.required and param.name not in parameters:
                raise ValueError(f"Missing required parameter: {param.name}")
        
        # 检查参数类型（简单验证）
        for param_name, param_value in parameters.items():
            param_def = next((p for p in schema.parameters if p.name == param_name), None)
            if param_def:
                if param_def.enum and param_value not in param_def.enum:
                    raise ValueError(f"Parameter {param_name} must be one of {param_def.enum}")
        
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取工具信息
        
        Returns:
            Dict[str, Any]: 工具信息
        """
        return {
            "name": self.name,
            "description": self.description,
            "type": self.tool_type.value,
            "initialized": self._initialized,
            "schema": self.get_schema().dict() if self._schema else None
        }
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            bool: 健康状态
        """
        return self._initialized


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, ToolBase] = {}
    
    def register(self, tool: ToolBase) -> bool:
        """
        注册工具
        
        Args:
            tool: 工具实例
            
        Returns:
            bool: 注册是否成功
        """
        if tool.name in self._tools:
            return False
        
        self._tools[tool.name] = tool
        return True
    
    def unregister(self, tool_name: str) -> bool:
        """
        注销工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 注销是否成功
        """
        if tool_name not in self._tools:
            return False
        
        del self._tools[tool_name]
        return True
    
    def get_tool(self, tool_name: str) -> Optional[ToolBase]:
        """
        获取工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            Optional[ToolBase]: 工具实例
        """
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """
        列出所有工具
        
        Returns:
            List[str]: 工具名称列表
        """
        return list(self._tools.keys())
    
    def get_all_tools(self) -> Dict[str, ToolBase]:
        """
        获取所有工具
        
        Returns:
            Dict[str, ToolBase]: 工具字典
        """
        return self._tools.copy()


# 全局工具注册表
tool_registry = ToolRegistry()
