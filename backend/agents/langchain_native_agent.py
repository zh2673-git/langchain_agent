"""
基于LangChain源码的原生Agent实现
完全按照LangChain官方源码和最佳实践实现
"""

import asyncio
from typing import Dict, Any, List, Optional, AsyncIterator, Union
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.tools import BaseTool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain.agents.format_scratchpad import format_to_tool_messages
from langchain.agents.output_parsers import ToolsAgentOutputParser
from langchain_community.chat_models import ChatOllama

from ..utils.logger import get_logger
from ..memory.memory_manager import MemoryManager
from ..tools.tool_manager import ToolManager
from ..config import config

logger = get_logger(__name__)


class LangChainNativeAgent:
    """
    基于LangChain源码的原生Agent实现
    
    完全按照LangChain官方文档和源码实现：
    1. 使用LangChain的标准Runnable接口
    2. 支持原生工具调用（如果模型支持）
    3. 支持流式输出
    4. 完全兼容LangChain生态系统
    """
    
    def __init__(self, provider: str = "ollama", model: str = "qwen2.5:7b"):
        self.provider = provider
        self.model = model
        self.model_name = model
        
        # LangChain组件
        self.llm = None
        self.memory_manager = None
        self.tool_manager = None
        
        # Agent组件
        self.agent = None
        self.agent_executor = None
        self.chain = None
        
        # 状态
        self.initialized = False
        
        logger.info(f"LangChainNativeAgent created for {provider}:{model}")
    
    async def initialize(self) -> bool:
        """初始化Agent - 完全按照LangChain最佳实践"""
        try:
            # 1. 初始化LLM - 使用LangChain标准方式
            if self.provider == "ollama":
                self.llm = ChatOllama(
                    model=self.model,
                    temperature=0.7,
                    streaming=True  # 启用流式输出
                )
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            # 2. 初始化内存管理器
            self.memory_manager = MemoryManager()
            await self.memory_manager.initialize()
            
            # 3. 初始化工具管理器
            self.tool_manager = ToolManager(self.llm, self.provider, self.model)
            await self._load_tools()
            
            # 4. 构建Agent - 使用LangChain标准方式
            await self._build_agent()
            
            self.initialized = True
            logger.info("LangChainNativeAgent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LangChainNativeAgent: {e}")
            return False
    
    async def _load_tools(self):
        """加载工具 - 使用LangChain标准工具接口"""
        from ..tools.tool_loader import ToolLoader

        tool_loader = ToolLoader()
        tools = await tool_loader.load_all_tools()
        for tool in tools:
            self.tool_manager.add_tool(tool)

        logger.info(f"Loaded {len(tools)} tools")
    
    async def _build_agent(self):
        """构建Agent - 完全按照LangChain源码实现"""
        
        # 检查模型是否支持工具调用
        supports_tools = config.model_supports_tools(self.provider, self.model)
        
        if supports_tools and self.tool_manager.get_langchain_tools():
            # 使用原生工具调用Agent
            await self._build_tool_calling_agent()
        else:
            # 使用基础对话链
            await self._build_conversation_chain()
    
    async def _build_tool_calling_agent(self):
        """构建工具调用Agent - 按照LangChain官方实现"""
        
        # 获取LangChain工具
        tools = self.tool_manager.get_langchain_tools()
        
        # 创建提示模板 - 按照LangChain标准
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. Use tools when appropriate."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # 绑定工具到LLM - LangChain标准方式
        llm_with_tools = self.llm.bind_tools(tools)
        
        # 创建Agent - 使用LangChain的create_tool_calling_agent
        self.agent = create_tool_calling_agent(llm_with_tools, tools, prompt)
        
        # 创建AgentExecutor - LangChain标准执行器
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=tools,
            verbose=True,
            return_intermediate_steps=True,
            handle_parsing_errors=True
        )
        
        logger.info("Tool calling agent built successfully")
    
    async def _build_conversation_chain(self):
        """构建对话链 - 按照LangChain Runnable接口"""
        
        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        # 构建链 - 使用LangChain的Runnable接口
        self.chain = (
            RunnablePassthrough.assign(
                chat_history=lambda x: self._get_chat_history(x.get("session_id"))
            )
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        logger.info("Conversation chain built successfully")
    
    def _get_chat_history(self, session_id: str) -> List[BaseMessage]:
        """获取聊天历史 - 返回LangChain标准Message对象（同步版本）"""
        if not session_id:
            return []

        try:
            # 使用简化的本地历史记录，避免async问题
            if hasattr(self, '_local_history'):
                history = self._local_history.get(session_id, [])
            else:
                self._local_history = {}
                history = []

            return history[-10:]  # 最近10条消息
        except Exception as e:
            logger.error(f"Failed to get chat history: {e}")
            return []
    
    async def chat(self, message: str, session_id: str = None, **kwargs) -> Dict[str, Any]:
        """聊天方法 - 完全按照LangChain标准实现"""
        try:
            if not self.initialized:
                return {"success": False, "error": "Agent not initialized"}
            
            # 准备输入 - LangChain标准格式
            input_data = {
                "input": message,
                "session_id": session_id
            }
            
            # 执行 - 使用LangChain标准方式
            if self.agent_executor:
                # 工具调用模式
                result = await self.agent_executor.ainvoke(input_data)
                response_content = result["output"]
                intermediate_steps = result.get("intermediate_steps", [])
                
                # 提取工具调用信息
                tool_calls = []
                for step in intermediate_steps:
                    if len(step) >= 2:
                        action, observation = step[0], step[1]
                        tool_calls.append({
                            "tool": action.tool,
                            "input": action.tool_input,
                            "result": str(observation),
                            "success": True
                        })
                
            else:
                # 对话模式
                result = await self.chain.ainvoke(input_data)
                response_content = result
                tool_calls = []
            
            # 保存到内存 - 使用LangChain标准Message对象
            if session_id:
                await self.memory_manager.add_message(
                    session_id, HumanMessage(content=message)
                )
                await self.memory_manager.add_message(
                    session_id, AIMessage(content=response_content)
                )
            
            return {
                "success": True,
                "content": response_content,
                "tool_calls": tool_calls,
                "thinking_process": "",  # 可以从中间步骤提取
                "model_info": {
                    "provider": self.provider,
                    "model": self.model,
                    "supports_tools": bool(self.agent_executor)
                }
            }
            
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"处理消息时出错: {str(e)}"
            }
    
    async def chat_stream(self, message: str, session_id: str = None, **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """流式聊天 - 完全按照LangChain流式接口实现"""
        try:
            if not self.initialized:
                yield {"success": False, "error": "Agent not initialized", "done": True}
                return
            
            # 准备输入
            input_data = {
                "input": message,
                "session_id": session_id
            }
            
            # 流式执行 - 使用LangChain的astream方法
            if self.agent_executor:
                # Agent流式执行
                async for chunk in self.agent_executor.astream(input_data):
                    if "output" in chunk:
                        yield {
                            "success": True,
                            "content": chunk["output"],
                            "done": False
                        }
                    elif "intermediate_step" in chunk:
                        # 工具调用步骤
                        step = chunk["intermediate_step"]
                        yield {
                            "success": True,
                            "content": f"🔧 调用工具: {step[0].tool}",
                            "done": False,
                            "tool_call": {
                                "tool": step[0].tool,
                                "input": step[0].tool_input
                            }
                        }
                
                yield {"success": True, "content": "", "done": True}
                
            else:
                # 链式流式执行
                full_response = ""
                async for chunk in self.chain.astream(input_data):
                    if chunk:
                        full_response += chunk
                        yield {
                            "success": True,
                            "content": chunk,
                            "done": False
                        }
                
                yield {"success": True, "content": "", "done": True}
                
                # 保存到内存
                if session_id:
                    await self.memory_manager.add_message(
                        session_id, HumanMessage(content=message)
                    )
                    await self.memory_manager.add_message(
                        session_id, AIMessage(content=full_response)
                    )
            
        except Exception as e:
            logger.error(f"Stream chat failed: {e}")
            yield {
                "success": False,
                "error": str(e),
                "content": f"流式处理出错: {str(e)}",
                "done": True
            }
    
    async def get_info(self) -> Dict[str, Any]:
        """获取Agent信息"""
        return {
            "type": "langchain_native",
            "provider": self.provider,
            "model": self.model,
            "initialized": self.initialized,
            "supports_tools": bool(self.agent_executor),
            "tools_count": len(self.tool_manager.list_tools()) if self.tool_manager else 0,
            "memory_enabled": bool(self.memory_manager)
        }
    
    async def clear_memory(self, session_id: str) -> bool:
        """清除内存"""
        if self.memory_manager:
            return await self.memory_manager.clear_session(session_id)
        return False
