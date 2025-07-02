"""
Chain方式的Agent实现
使用LangChain的Chain组合方式实现多轮对话、工具调用、记忆管理

核心特点：
1. 使用Runnable接口组合各种组件
2. 支持流式输出
3. 灵活的链式组合
4. 完全基于LangChain标准实现
"""

import asyncio
from typing import Dict, Any, List, Optional, AsyncIterator
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableParallel
try:
    from langchain_ollama import ChatOllama
except ImportError:
    from langchain_community.chat_models import ChatOllama

from ..utils.logger import get_logger
from ..tools.tool_service import get_tool_service, initialize_tool_service
from ..memory.memory_service import get_memory_service, initialize_memory_service
from ..config import config

logger = get_logger(__name__)


class ChainAgent:
    """
    基于Chain的Agent实现
    
    使用LangChain的Runnable接口组合实现：
    1. 多轮对话管理
    2. 工具调用（通过提示词方式）
    3. 记忆管理
    4. 流式输出支持
    """
    
    def __init__(self, provider: str = "ollama", model: str = "qwen2.5:7b"):
        self.provider = provider
        self.model = model
        
        # 核心组件
        self.llm = None
        self.tool_service = get_tool_service()
        self.memory_service = get_memory_service()
        
        # Chain组件
        self.conversation_chain = None
        self.tool_chain = None
        self.main_chain = None
        
        # 状态
        self.initialized = False
        
        logger.info(f"ChainAgent created for {provider}:{model}")

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
            
            # 3. 构建Chain
            await self._build_chains()

            self.initialized = True
            logger.info("ChainAgent initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize ChainAgent: {e}")
            return False
    
    async def _build_chains(self):
        """构建Chain组合"""
        
        # 1. 对话Chain - 处理普通对话
        conversation_prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        self.conversation_chain = (
            RunnablePassthrough.assign(
                chat_history=RunnableLambda(self._get_chat_history),
                tools_description=RunnableLambda(lambda x: self.tool_service.get_tools_description())
            )
            | conversation_prompt
            | self.llm
            | StrOutputParser()
        )
        
        # 2. 工具Chain - 处理工具调用
        self.tool_chain = RunnableLambda(self._handle_tool_calls)
        
        # 2. 工具Chain - 处理工具调用
        self.tool_chain = RunnableLambda(self._handle_tool_calls)

        # 3. 主Chain - 组合对话和工具调用
        async def process_main_chain(inputs):
            # 先执行对话
            response = await self.conversation_chain.ainvoke(inputs)
            # 然后处理工具调用
            return await self._process_response({"response": response})

        self.main_chain = RunnableLambda(process_main_chain)
        
        logger.info("Chains built successfully")
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个智能助手，可以进行对话并使用工具来帮助用户。

当你需要使用工具时，请按照以下格式：
TOOL_CALL: 工具名称
参数: {{"参数名": "参数值"}}

可用工具：
{tools_description}

请根据用户的问题选择合适的工具，或直接回答问题。"""
    
    def _get_chat_history(self, inputs: Dict[str, Any]) -> List[BaseMessage]:
        """获取聊天历史"""
        session_id = inputs.get("session_id")
        if not session_id:
            return []
        
        try:
            # 通过记忆服务获取聊天历史
            return self.memory_service.get_chat_history_sync(session_id, limit=10)
        except Exception as e:
            logger.error(f"Failed to get chat history: {e}")
            return []
    
    async def _process_response(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """处理响应，检查是否需要工具调用"""
        response = inputs.get("response", "")

        # 检查是否包含工具调用
        if "TOOL_CALL:" in response:
            return await self._handle_tool_calls(inputs)
        else:
            return {
                "content": response,
                "tool_calls": [],
                "success": True
            }
    
    async def _handle_tool_calls(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具调用"""
        response = inputs.get("response", "")
        tool_calls = []
        
        try:
            # 解析工具调用
            lines = response.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith("TOOL_CALL:"):
                    tool_name = line.replace("TOOL_CALL:", "").strip()
                    
                    # 查找参数
                    params = {}
                    if i + 1 < len(lines) and lines[i + 1].strip().startswith("参数:"):
                        try:
                            import json
                            params_str = lines[i + 1].replace("参数:", "").strip()
                            params = json.loads(params_str)
                        except:
                            params = {}
                    
                    # 执行工具
                    result = await self.tool_service.execute_tool(tool_name, **params)
                    tool_calls.append({
                        "tool": tool_name,
                        "input": params,
                        "result": result.get("result", ""),
                        "success": result.get("success", False)
                    })
                
                i += 1
            
            # 如果有工具调用，生成包含工具结果的响应
            if tool_calls:
                tool_results = []
                for call in tool_calls:
                    tool_results.append(f"工具 {call['tool']} 执行结果：{call['result']}")
                
                final_response = response + "\n\n" + "\n".join(tool_results)
            else:
                final_response = response
            
            return {
                "content": final_response,
                "tool_calls": tool_calls,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Tool call handling failed: {e}")
            return {
                "content": response,
                "tool_calls": [],
                "success": True,
                "error": str(e)
            }
    
    async def chat(self, message: str, session_id: str = None, **kwargs) -> Dict[str, Any]:
        """聊天方法"""
        try:
            if not self.initialized:
                return {"success": False, "error": "Agent not initialized"}
            
            # 准备输入
            input_data = {
                "input": message,
                "session_id": session_id
            }
            
            # 执行主Chain
            result = await self.main_chain.ainvoke(input_data)
            
            # 保存到内存
            if session_id:
                await self.memory_service.add_message(
                    session_id, HumanMessage(content=message)
                )
                await self.memory_service.add_message(
                    session_id, AIMessage(content=result["content"])
                )
            
            return {
                "success": True,
                "content": result["content"],
                "tool_calls": result.get("tool_calls", []),
                "model_info": {
                    "provider": self.provider,
                    "model": self.model,
                    "type": "chain"
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
            
            input_data = {
                "input": message,
                "session_id": session_id
            }
            
            # 流式执行
            full_response = ""
            async for chunk in self.conversation_chain.astream(input_data):
                if chunk:
                    full_response += chunk
                    yield {
                        "success": True,
                        "content": chunk,
                        "done": False
                    }
            
            # 处理工具调用
            if "TOOL_CALL:" in full_response:
                tool_result = await self._handle_tool_calls({"response": full_response})
                if tool_result.get("tool_calls"):
                    for call in tool_result["tool_calls"]:
                        yield {
                            "success": True,
                            "content": f"\n🔧 执行工具: {call['tool']} -> {call['result']}",
                            "done": False,
                            "tool_call": call
                        }
            
            yield {"success": True, "content": "", "done": True}
            
            # 保存到内存
            if session_id:
                await self.memory_service.add_message(
                    session_id, HumanMessage(content=message)
                )
                await self.memory_service.add_message(
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
            "type": "chain",
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
                # 重新构建chains
                await self._build_chains()
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
            "agent_type": "chain",
            "initialized": self.initialized
        }
