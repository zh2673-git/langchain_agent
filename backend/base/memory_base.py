"""
记忆管理基类定义
定义记忆和会话管理的通用接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel
from datetime import datetime


class Message(BaseModel):
    """消息模型"""
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = None
    metadata: Dict[str, Any] = {}
    
    def __init__(self, **data):
        if data.get('timestamp') is None:
            data['timestamp'] = datetime.now()
        super().__init__(**data)


class Session(BaseModel):
    """会话模型"""
    session_id: str
    created_at: datetime
    updated_at: datetime
    messages: List[Message] = []
    metadata: Dict[str, Any] = {}


class MemoryBase(ABC):
    """记忆管理基类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化记忆管理器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化记忆管理器
        
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    async def create_session(self, session_id: str = None, metadata: Dict[str, Any] = None) -> str:
        """
        创建新会话
        
        Args:
            session_id: 会话 ID，如果为 None 则自动生成
            metadata: 会话元数据
            
        Returns:
            str: 会话 ID
        """
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        获取会话信息
        
        Args:
            session_id: 会话 ID
            
        Returns:
            Optional[Session]: 会话信息
        """
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """
        删除会话
        
        Args:
            session_id: 会话 ID
            
        Returns:
            bool: 删除是否成功
        """
        pass
    
    @abstractmethod
    async def list_sessions(self, limit: int = 100, offset: int = 0) -> List[Session]:
        """
        列出会话
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            List[Session]: 会话列表
        """
        pass
    
    @abstractmethod
    async def add_message(self, session_id: str, message: Message) -> bool:
        """
        添加消息到会话
        
        Args:
            session_id: 会话 ID
            message: 消息对象
            
        Returns:
            bool: 添加是否成功
        """
        pass
    
    @abstractmethod
    async def get_messages(self, session_id: str, limit: int = 100, offset: int = 0) -> List[Message]:
        """
        获取会话消息
        
        Args:
            session_id: 会话 ID
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            List[Message]: 消息列表
        """
        pass
    
    @abstractmethod
    async def clear_messages(self, session_id: str) -> bool:
        """
        清除会话消息
        
        Args:
            session_id: 会话 ID
            
        Returns:
            bool: 清除是否成功
        """
        pass
    
    @abstractmethod
    async def search_messages(self, query: str, session_id: str = None, limit: int = 10) -> List[Message]:
        """
        搜索消息
        
        Args:
            query: 搜索查询
            session_id: 会话 ID，如果为 None 则搜索所有会话
            limit: 限制数量
            
        Returns:
            List[Message]: 匹配的消息列表
        """
        pass
    
    async def get_conversation_summary(self, session_id: str) -> Optional[str]:
        """
        获取对话摘要
        
        Args:
            session_id: 会话 ID
            
        Returns:
            Optional[str]: 对话摘要
        """
        messages = await self.get_messages(session_id)
        if not messages:
            return None
        
        # 简单的摘要生成逻辑
        total_messages = len(messages)
        user_messages = len([m for m in messages if m.role == "user"])
        assistant_messages = len([m for m in messages if m.role == "assistant"])
        
        return f"对话包含 {total_messages} 条消息，其中用户消息 {user_messages} 条，助手回复 {assistant_messages} 条"
