"""
LangGraph方式的Agent实现
使用LangGraph实现更复杂的工作流和状态管理

核心特点：
1. 使用LangGraph构建状态图
2. 支持复杂的工作流控制
3. 状态管理和持久化
4. 支持条件分支和循环
"""

from typing import Dict, Any, List, Optional, AsyncIterator, TypedDict, Annotated
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
try:
    from langchain_ollama import ChatOllama
except ImportError:
    from langchain_community.chat_models import ChatOllama

try:
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolNode
    from langgraph.checkpoint.memory import MemorySaver
    # 尝试导入add_messages，如果失败则定义一个简单版本
    try:
        from langgraph.graph.message import add_messages
    except ImportError:
        def add_messages(left, right):
            """简单的消息合并函数"""
            return left + right
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    # 创建模拟类以避免导入错误
    class StateGraph:
        def __init__(self, *args, **kwargs):
            pass
        def add_node(self, *args, **kwargs):
            pass
        def add_edge(self, *args, **kwargs):
            pass
        def add_conditional_edges(self, *args, **kwargs):
            pass
        def set_entry_point(self, *args, **kwargs):
            pass
        def compile(self, *args, **kwargs):
            return self

    class ToolNode:
        def __init__(self, *args, **kwargs):
            pass

    class MemorySaver:
        def __init__(self, *args, **kwargs):
            pass

    END = "END"

    def add_messages(left, right):
        return left + right

from ..utils.logger import get_logger
from ..tools.tool_service import get_tool_service, initialize_tool_service
from ..memory.memory_service import get_memory_service, initialize_memory_service
from ..config import config

logger = get_logger(__name__)


class AgentState(TypedDict):
    """Agent状态定义"""
    messages: Annotated[List[BaseMessage], add_messages]
    session_id: str
    tool_calls: List[Dict[str, Any]]
    iteration_count: int


class LangGraphAgent:
    """
    基于LangGraph的Agent实现
    
    使用LangGraph构建复杂的状态图：
    1. 支持复杂工作流控制
    2. 状态管理和持久化
    3. 条件分支和循环
    4. 工具调用管理
    """
    
    def __init__(self, provider: str = "ollama", model: str = "qwen2.5:7b"):
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph not available. Please install with: pip install langgraph")
        
        self.provider = provider
        self.model = model
        
        # 核心组件
        self.llm = None
        self.tool_service = get_tool_service()
        self.memory_service = get_memory_service()
        
        # LangGraph组件
        self.graph = None
        self.checkpointer = None
        
        # 状态
        self.initialized = False
        
        logger.info(f"LangGraphAgent created for {provider}:{model}")

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
            # 检查LangGraph是否可用
            if not LANGGRAPH_AVAILABLE:
                logger.error("LangGraph is not available. Please install langgraph: pip install langgraph")
                return False

            # 1. 初始化LLM
            success = await self._initialize_llm()
            if not success:
                return False

            # 2. 初始化服务
            await initialize_memory_service()
            await initialize_tool_service(self.llm, self.provider, self.model)
            
            # 3. 加载工具
            await self._load_tools()
            
            # 4. 构建LangGraph
            await self._build_graph()
            
            self.initialized = True
            logger.info("LangGraphAgent initialized successfully")
            return True
            
        except Exception as e:
            import traceback
            logger.error(f"Failed to initialize LangGraphAgent: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    async def _load_tools(self):
        """加载工具"""
        # 直接使用工具服务，无需单独加载
        tools = self.tool_service.get_tools()
        logger.info(f"Using {len(tools)} tools from tool service")
    
    async def _build_graph(self):
        """构建LangGraph状态图"""
        
        # 创建状态图
        workflow = StateGraph(AgentState)
        
        # 获取工具
        tools = self.tool_service.get_tools()
        
        # 绑定工具到LLM
        try:
            if tools and hasattr(self.llm, 'bind_tools'):
                self.llm_with_tools = self.llm.bind_tools(tools)
                logger.info("Successfully bound tools to LLM for LangGraph")
            else:
                self.llm_with_tools = self.llm
                logger.warning("LLM does not support tool binding, using without tools")
                tools = []
        except NotImplementedError:
            logger.warning("LLM does not support bind_tools for LangGraph")
            self.llm_with_tools = self.llm
            tools = []
        except Exception as e:
            logger.error(f"Failed to bind tools in LangGraph: {e}")
            self.llm_with_tools = self.llm
            tools = []
            
            # 创建工具节点
            tool_node = ToolNode(tools)
            
            # 添加节点
            workflow.add_node("agent", self._call_model)
            workflow.add_node("tools", tool_node)
            
            # 设置入口点
            workflow.set_entry_point("agent")
            
            # 添加条件边
            workflow.add_conditional_edges(
                "agent",
                self._should_continue,
                {
                    "continue": "tools",
                    "end": END,
                }
            )
            
            # 工具执行后回到agent
            workflow.add_edge("tools", "agent")
            
        else:
            # 没有工具的简单对话模式
            workflow.add_node("agent", self._call_model)
            workflow.set_entry_point("agent")
            workflow.add_edge("agent", END)
        
        # 创建检查点保存器
        self.checkpointer = MemorySaver()
        
        # 编译图
        self.graph = workflow.compile(checkpointer=self.checkpointer)
        
        logger.info("LangGraph built successfully")
    
    def _call_model(self, state: AgentState) -> Dict[str, Any]:
        """调用模型"""
        messages = state["messages"]

        # 调用模型 - 直接传递消息列表
        if hasattr(self, 'llm_with_tools'):
            response = self.llm_with_tools.invoke(messages)
        else:
            response = self.llm.invoke(messages)

        return {"messages": [response]}
    
    def _should_continue(self, state: AgentState) -> str:
        """决定是否继续执行工具"""
        messages = state["messages"]
        last_message = messages[-1]
        
        # 检查是否有工具调用
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"
        else:
            return "end"
    
    async def chat(self, message: str, session_id: str = None, **kwargs) -> Dict[str, Any]:
        """聊天方法"""
        try:
            if not self.initialized:
                return {"success": False, "error": "Agent not initialized"}
            
            # 获取历史消息
            chat_history = []
            if session_id and self.memory_service:
                history = await self.memory_service.get_chat_history(session_id, limit=10)
                chat_history = history

            # 准备初始状态
            all_messages = chat_history + [HumanMessage(content=message)]
            initial_state = {
                "messages": all_messages,
                "session_id": session_id or "default",
                "tool_calls": [],
                "iteration_count": 0
            }
            
            # 配置
            config_dict = {"configurable": {"thread_id": session_id or "default"}}
            
            # 执行图
            result = await self.graph.ainvoke(initial_state, config=config_dict)
            
            # 提取响应
            messages = result["messages"]
            last_message = messages[-1] if messages else None
            
            if last_message:
                response_content = last_message.content
                
                # 提取工具调用信息
                tool_calls = []
                if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                    for tool_call in last_message.tool_calls:
                        tool_calls.append({
                            "tool": tool_call.get("name", "unknown"),
                            "input": tool_call.get("args", {}),
                            "result": "Tool executed",
                            "success": True
                        })
            else:
                response_content = "No response generated"
                tool_calls = []
            
            # 保存到内存
            if session_id and self.memory_service:
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
                    "type": "langgraph"
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
            
            # 准备初始状态
            initial_state = {
                "messages": [HumanMessage(content=message)],
                "session_id": session_id or "default",
                "tool_calls": [],
                "iteration_count": 0
            }
            
            # 配置
            config_dict = {"configurable": {"thread_id": session_id or "default"}}
            
            # 流式执行
            full_response = ""
            async for chunk in self.graph.astream(initial_state, config=config_dict):
                for node_name, node_output in chunk.items():
                    if "messages" in node_output:
                        messages = node_output["messages"]
                        if messages:
                            last_message = messages[-1]
                            if hasattr(last_message, 'content') and last_message.content:
                                content = last_message.content
                                if content != full_response:
                                    new_content = content[len(full_response):]
                                    full_response = content
                                    yield {
                                        "success": True,
                                        "content": new_content,
                                        "done": False
                                    }
                            
                            # 检查工具调用
                            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                                for tool_call in last_message.tool_calls:
                                    yield {
                                        "success": True,
                                        "content": f"\n🔧 调用工具: {tool_call.get('name', 'unknown')}",
                                        "done": False,
                                        "tool_call": {
                                            "tool": tool_call.get('name', 'unknown'),
                                            "input": tool_call.get('args', {})
                                        }
                                    }
            
            yield {"success": True, "content": "", "done": True}
            
            # 保存到内存
            if session_id and self.memory_manager:
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
            "type": "langgraph",
            "provider": self.provider,
            "model": self.model,
            "initialized": self.initialized,
            "supports_tools": True,
            "tools_count": len(self.tool_manager.get_tools()) if self.tool_manager else 0,
            "memory_enabled": bool(self.memory_manager),
            "langgraph_available": LANGGRAPH_AVAILABLE
        }
    
    async def clear_memory(self, session_id: str) -> bool:
        """清除内存"""
        if self.memory_manager:
            return await self.memory_manager.clear_session(session_id)
        return False

    async def switch_model(self, new_model: str) -> bool:
        """切换底层模型"""
        try:
            old_model = self.model
            self.model = new_model

            # 重新初始化LLM
            success = await self._initialize_llm()
            if success:
                # 重新构建graph
                await self._build_graph()
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
            "agent_type": "langgraph",
            "initialized": self.initialized
        }
