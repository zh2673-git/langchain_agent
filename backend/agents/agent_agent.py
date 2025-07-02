"""
基于LangChain原生Agent实现
使用create_tool_calling_agent和AgentExecutor实现标准的LangChain Agent

核心特点：
1. 使用LangChain标准的create_tool_calling_agent
2. 支持原生工具调用（function calling）
3. 使用AgentExecutor管理执行流程
4. 完全兼容LangChain生态系统
"""

import asyncio
from typing import Dict, Any, List, Optional, AsyncIterator
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.tools import BaseTool
from langchain.agents import create_tool_calling_agent, AgentExecutor
try:
    from langchain_ollama import ChatOllama
except ImportError:
    from langchain_community.chat_models import ChatOllama

from ..utils.logger import get_logger
from ..tools.tool_service import get_tool_service, initialize_tool_service
from ..memory.memory_service import get_memory_service, initialize_memory_service
from ..config import config

logger = get_logger(__name__)


class AgentAgent:
    """
    基于LangChain原生Agent实现
    
    使用LangChain标准的create_tool_calling_agent和AgentExecutor：
    1. 支持原生工具调用（function calling）
    2. 使用AgentExecutor管理执行流程
    3. 支持流式输出
    4. 完全兼容LangChain生态系统
    """
    
    def __init__(self, provider: str = "ollama", model: str = "qwen2.5:7b"):
        self.provider = provider
        self.model = model
        
        # LangChain组件
        self.llm = None
        self.tool_service = get_tool_service()
        self.memory_service = get_memory_service()
        
        # Agent组件
        self.agent = None
        self.agent_executor = None
        
        # 状态
        self.initialized = False
        
        logger.info(f"AgentAgent created for {provider}:{model}")

    async def _initialize_llm(self) -> bool:
        """初始化LLM"""
        try:
            if self.provider == "ollama":
                self.llm = ChatOllama(
                    model=self.model,
                    temperature=0.7,
                    streaming=True,
                    base_url=config.OLLAMA_BASE_URL
                )
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            logger.info(f"LLM initialized: {self.provider}:{self.model}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            return False

    async def initialize(self) -> bool:
        """初始化Agent"""
        try:
            # 1. 初始化LLM
            success = await self._initialize_llm()
            if not success:
                return False

            # 2. 初始化服务
            await initialize_memory_service()
            await initialize_tool_service(self.llm, self.provider, self.model)
            
            # 3. 构建Agent - 使用LangChain标准方式
            await self._build_agent()
            
            self.initialized = True
            logger.info("AgentAgent initialized successfully")
            return True
            
        except Exception as e:
            import traceback
            logger.error(f"Failed to initialize AgentAgent: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    async def _build_agent(self):
        """构建Agent - 完全按照LangChain标准实现"""
        
        # 检查模型是否支持工具调用
        supports_tools = config.model_supports_tools(self.provider, self.model)
        
        if supports_tools and self.tool_service.get_tools():
            # 使用原生工具调用Agent
            await self._build_tool_calling_agent()
        else:
            # 使用基础对话链
            await self._build_conversation_chain()
    
    async def _build_tool_calling_agent(self):
        """构建工具调用Agent - 按照LangChain官方实现"""

        # 获取LangChain工具
        tools = self.tool_service.get_tools()
        logger.info(f"AgentAgent: Got {len(tools)} tools from tool service")

        # 验证工具
        valid_tools = []
        for tool in tools:
            if hasattr(tool, 'name') and hasattr(tool, 'description'):
                valid_tools.append(tool)
                logger.debug(f"Valid tool: {tool.name}")
            else:
                logger.warning(f"Invalid tool: {tool}")

        logger.info(f"AgentAgent: Using {len(valid_tools)} valid tools")

        # 创建提示模板 - 按照LangChain标准
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. Use tools when appropriate to help the user."),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # 创建Agent - 使用LangChain的create_tool_calling_agent
        # 注意：对于不支持工具调用的模型，LangChain会自动使用提示词方式
        self.agent = create_tool_calling_agent(self.llm, valid_tools, prompt)

        # 创建AgentExecutor - LangChain标准执行器
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=valid_tools,
            verbose=True,
            return_intermediate_steps=True,
            handle_parsing_errors=True,
            max_iterations=5  # 限制最大迭代次数
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
        from langchain_core.runnables import RunnablePassthrough
        from langchain_core.output_parsers import StrOutputParser
        
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
        """获取聊天历史"""
        if not session_id:
            return []
        
        try:
            return self.memory_service.get_chat_history_sync(session_id, limit=10)
        except Exception as e:
            logger.error(f"Failed to get chat history: {e}")
            return []
    
    async def chat(self, message: str, session_id: str = None, **kwargs) -> Dict[str, Any]:
        """聊天方法"""
        try:
            if not self.initialized:
                return {"success": False, "error": "Agent not initialized"}
            
            # 准备输入
            input_data = {
                "input": message,
                "chat_history": self._get_chat_history(session_id)
            }
            
            # 执行Agent或Chain
            if self.agent_executor:
                # 使用AgentExecutor
                result = await self.agent_executor.ainvoke(input_data)
                response_content = result.get("output", "")
                
                # 提取工具调用信息
                tool_calls = []
                intermediate_steps = result.get("intermediate_steps", [])
                for step in intermediate_steps:
                    if len(step) >= 2:
                        action, observation = step
                        tool_calls.append({
                            "tool": action.tool,
                            "input": action.tool_input,
                            "result": str(observation),
                            "success": True
                        })
            
            elif self.chain:
                # 使用对话链
                response_content = await self.chain.ainvoke(input_data)
                tool_calls = []
            
            else:
                return {"success": False, "error": "No agent or chain available"}
            
            # 保存到内存
            if session_id:
                await self.memory_service.add_message(
                    session_id, HumanMessage(content=message)
                )
                await self.memory_service.add_message(
                    session_id, AIMessage(content=response_content)
                )
            
            return {
                "success": True,
                "content": response_content,
                "tool_calls": tool_calls,
                "model_info": {
                    "provider": self.provider,
                    "model": self.model,
                    "type": "agent"
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
        """流式聊天"""
        try:
            if not self.initialized:
                yield {"success": False, "error": "Agent not initialized", "done": True}
                return
            
            # 对于Agent模式，先执行完整对话，然后流式返回
            response = await self.chat(message, session_id, **kwargs)
            
            if response.get("success"):
                content = response.get("content", "")
                
                # 模拟流式输出
                words = content.split()
                for i, word in enumerate(words):
                    yield {
                        "success": True,
                        "content": word + " ",
                        "done": False
                    }
                    await asyncio.sleep(0.01)  # 小延迟模拟流式
                
                # 输出工具调用信息
                tool_calls = response.get("tool_calls", [])
                for call in tool_calls:
                    yield {
                        "success": True,
                        "content": f"\n🔧 工具调用: {call['tool']} -> {call['result']}",
                        "done": False,
                        "tool_call": call
                    }
            
            yield {"success": True, "content": "", "done": True}
            
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
            "type": "agent",
            "provider": self.provider,
            "model": self.model,
            "initialized": self.initialized,
            "supports_tools": True,
            "tools_count": len(self.tool_service.get_tools()),
            "memory_enabled": True
        }
    
    async def clear_memory(self, session_id: str) -> bool:
        """清除内存"""
        return await self.memory_service.clear_session(session_id)

    async def switch_model(self, new_model: str) -> bool:
        """切换底层模型"""
        try:
            old_model = self.model
            self.model = new_model

            # 重新初始化LLM
            success = await self._initialize_llm()
            if success:
                # 重新构建agent
                await self._build_agent()
                logger.info(f"Successfully switched from {old_model} to {new_model}")
                return True
            else:
                # 恢复原模型
                self.model = old_model
                logger.error(f"Failed to switch to {new_model}, reverted to {old_model}")
                return False

        except Exception as e:
            logger.error(f"Error switching model: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "current_model": self.model,
            "provider": self.provider,
            "agent_type": "agent",
            "initialized": self.initialized
        }
