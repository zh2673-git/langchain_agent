"""
Agent 基类定义
定义所有 Agent 实现的通用接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel


class AgentResponse(BaseModel):
    """Agent 响应模型"""
    success: bool = True
    content: str
    metadata: Dict[str, Any] = {}
    tool_calls: List[Dict[str, Any]] = []
    error: Optional[str] = None
    thinking_process: Optional[str] = None  # 推理过程
    execution_steps: List[Dict[str, Any]] = []  # 执行步骤


class AgentBase(ABC):
    """Agent 基类"""
    
    def __init__(self, name: str, config: Dict[str, Any] = None):
        """
        初始化 Agent
        
        Args:
            name: Agent 名称
            config: Agent 配置
        """
        self.name = name
        self.config = config or {}
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化 Agent
        
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    async def chat(self, message: str, session_id: str = None, **kwargs) -> AgentResponse:
        """
        与 Agent 对话
        
        Args:
            message: 用户消息
            session_id: 会话 ID
            **kwargs: 其他参数
            
        Returns:
            AgentResponse: Agent 响应
        """
        pass
    
    @abstractmethod
    async def chat_stream(self, message: str, session_id: str = None, **kwargs):
        """
        流式对话
        
        Args:
            message: 用户消息
            session_id: 会话 ID
            **kwargs: 其他参数
            
        Yields:
            str: 流式响应内容
        """
        pass
    
    @abstractmethod
    def add_tool(self, tool: Any) -> bool:
        """
        添加工具
        
        Args:
            tool: 工具实例
            
        Returns:
            bool: 添加是否成功
        """
        pass
    
    @abstractmethod
    def remove_tool(self, tool_name: str) -> bool:
        """
        移除工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            bool: 移除是否成功
        """
        pass
    
    @abstractmethod
    def list_tools(self) -> List[str]:
        """
        列出所有工具
        
        Returns:
            List[str]: 工具名称列表
        """
        pass
    
    @abstractmethod
    def get_memory(self, session_id: str = None) -> Dict[str, Any]:
        """
        获取记忆信息
        
        Args:
            session_id: 会话 ID
            
        Returns:
            Dict[str, Any]: 记忆信息
        """
        pass
    
    @abstractmethod
    async def clear_memory(self, session_id: str = None) -> bool:
        """
        清除记忆
        
        Args:
            session_id: 会话 ID
            
        Returns:
            bool: 清除是否成功
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取 Agent 信息
        
        Returns:
            Dict[str, Any]: Agent 信息
        """
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "config": self.config,
            "initialized": self._initialized,
            "tools": self.list_tools()
        }
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            bool: 健康状态
        """
        return self._initialized
