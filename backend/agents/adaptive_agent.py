"""
智能自适应 Agent 实现
根据用户需求和模型能力自动选择最佳处理策略的智能Agent

这个Agent会：
1. 自动检测模型是否支持原生工具调用
2. 根据任务复杂度选择合适的处理方式
3. 智能切换Chain、Agent、LangGraph模式
4. 提供统一的接口和最佳的用户体验

模式说明：
- Chain模式：简单快速，适合基础对话
- Agent模式：智能推理，适合复杂任务
- LangGraph模式：状态管理，适合工作流
- Adaptive模式：智能选择，自动适配最佳策略
"""
import asyncio
from typing import Dict, Any, List, AsyncGenerator

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.chat_models import ChatOllama

from ..base.agent_base import AgentBase, AgentResponse
from ..memory.memory_manager import create_memory_manager
from ..config import config
from ..utils.logger import get_logger
from ..tools.tool_manager import ToolManager

logger = get_logger(__name__)


class AdaptiveAgent(AgentBase):
    """智能自适应 Agent
    
    特点：
    - 自动检测模型能力并选择最佳策略
    - 根据任务复杂度智能切换处理模式
    - 支持原生工具调用和提示词工具调用
    - 提供流式输出和开发者模式信息
    - 统一的接口，最佳的用户体验
    """
    
    def __init__(self, name: str = "adaptive_agent"):
        super().__init__(name=name)
        self.llm = None
        self.chain = None
        self.agent_executor = None
        self.tool_manager = None
        self.memory_manager = None
        self._initialized = False
        self.current_mode = "adaptive"  # adaptive, chain, agent, langgraph
    
    async def initialize(self, model_config: Dict[str, Any] = None) -> bool:
        """初始化自适应 Agent"""
        try:
            # 使用提供的配置或默认配置
            if model_config:
                self.model_config = model_config
            else:
                self.model_config = {
                    "provider": config.DEFAULT_MODEL_PROVIDER,
                    "model": config.DEFAULT_MODEL_NAME,
                    "temperature": config.DEFAULT_TEMPERATURE
                }
            
            # 初始化 LLM
            self.llm = ChatOllama(
                model=self.model_config["model"],
                temperature=self.model_config.get("temperature", 0.7),
                base_url=config.OLLAMA_BASE_URL
            )

            # 初始化工具管理器
            self.tool_manager = ToolManager(
                llm=self.llm,
                provider=self.model_config['provider'],
                model=self.model_config['model']
            )
            
            # 初始化内存管理器
            self.memory_manager = create_memory_manager()
            await self.memory_manager.initialize()
            
            # 加载工具
            await self._initialize_tools()
            
            # 构建处理链
            self._build_processing_chain()
            
            self._initialized = True
            logger.info(f"AdaptiveAgent initialized successfully")
            logger.info(f"Model supports native tools: {self.tool_manager.supports_native_tools}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AdaptiveAgent: {e}")
            return False
    
    async def _initialize_tools(self):
        """初始化工具"""
        from ..tools.tool_loader import auto_load_tools

        tools = await auto_load_tools()
        for tool in tools:
            self.tool_manager.add_tool(tool)

        logger.info(f"Loaded {len(tools)} tools")
    
    def _build_processing_chain(self):
        """根据模型能力构建处理链"""
        # 暂时统一使用提示词方式，确保稳定性
        logger.info(f"Model supports native tools: {self.tool_manager.supports_native_tools}")
        logger.info("Using prompt-based tool calling for stability")
        self._build_prompt_tool_chain()
    
    def _build_prompt_tool_chain(self):
        """构建基于提示词的工具调用链"""
        logger.info("Building prompt-based tool calling chain")
        
        # 获取工具描述
        tools_description = self.tool_manager.get_tools_description()
        
        # 构建系统提示词，正确转义大括号避免模板变量冲突
        system_prompt = """你是一个智能助手，能够使用各种工具来帮助用户。

当你需要使用工具时，请按照以下格式：
TOOL_CALL: {{{{
    "tool": "工具名称",
    "input": "工具输入参数"
}}}}

可用的工具：
""" + tools_description + """

请根据用户的问题，决定是否需要使用工具。如果需要，请选择合适的工具并提供正确的参数。
如果不需要使用工具，请直接回答用户的问题。

请用中文回答，保持友好和专业的语调。"""
        
        # 创建提示词模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        # 创建处理链
        self.chain = prompt | self.llm | StrOutputParser()
        
        logger.info("Prompt-based tool calling chain built successfully")
    
    async def chat(self, message: str, session_id: str = None, **kwargs) -> AgentResponse:
        """智能对话 - 自动选择最佳处理策略"""
        try:
            if not self._initialized:
                await self.initialize()
            
            # 分析任务复杂度并选择处理模式
            processing_mode = self._analyze_task_complexity(message)
            
            # 获取聊天历史
            chat_history = await self._get_chat_history(session_id)
            
            # 根据选择的模式处理
            if processing_mode == "simple":
                response = await self._process_simple_task(message, session_id, chat_history)
            elif processing_mode == "complex":
                response = await self._process_complex_task(message, session_id, chat_history)
            else:
                response = await self._process_with_prompt_tools(message, session_id, chat_history)
            
            return response
            
        except Exception as e:
            logger.error(f"Adaptive chat failed: {e}")
            return AgentResponse(
                success=False,
                content="",
                error=str(e)
            )
    
    def _analyze_task_complexity(self, message: str) -> str:
        """分析任务复杂度"""
        # 简单的启发式分析
        complex_keywords = ["计算", "搜索", "文件", "查看", "分析", "处理", "工具"]
        simple_keywords = ["你好", "介绍", "什么", "怎么样", "谢谢"]
        
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in complex_keywords):
            return "complex"
        elif any(keyword in message_lower for keyword in simple_keywords):
            return "simple"
        else:
            return "adaptive"
    
    async def _process_simple_task(self, message: str, session_id: str, chat_history: List) -> AgentResponse:
        """处理简单任务 - 使用Chain模式"""
        try:
            # 简单的对话处理
            input_data = {
                "input": message,
                "chat_history": chat_history
            }
            
            response = await self.chain.ainvoke(input_data)
            
            # 保存对话到内存
            if session_id:
                await self.memory_manager.add_message(session_id, HumanMessage(content=message))
                await self.memory_manager.add_message(session_id, AIMessage(content=response))
            
            return AgentResponse(
                success=True,
                content=response,
                metadata={
                    "processing_mode": "simple",
                    "agent_type": "adaptive",
                    "model": self.model_config["model"]
                }
            )
            
        except Exception as e:
            logger.error(f"Simple task processing failed: {e}")
            raise
    
    async def _process_complex_task(self, message: str, session_id: str, chat_history: List) -> AgentResponse:
        """处理复杂任务 - 使用Agent模式"""
        return await self._process_with_prompt_tools(message, session_id, chat_history)
    
    async def _process_with_prompt_tools(self, message: str, session_id: str, chat_history: List) -> AgentResponse:
        """使用提示词工具处理"""
        try:
            # 调用链获取响应
            input_data = {
                "input": message,
                "chat_history": chat_history
            }
            
            response = await self.chain.ainvoke(input_data)
            
            # 检查是否需要调用工具
            tool_calls = []
            if self._should_call_tools(response):
                tool_calls = self._extract_tool_calls(response)
                
                # 执行工具调用
                for tool_call in tool_calls:
                    result = await self._execute_tool_call(tool_call)
                    tool_call.update(result)
                
                # 如果有工具调用，重新生成响应
                if tool_calls:
                    tool_results = "\n".join([f"工具 {tc['tool']} 执行结果: {tc['result']}" for tc in tool_calls])
                    final_input = f"{message}\n\n工具执行结果:\n{tool_results}\n\n请根据以上信息给出最终回答："
                    
                    final_response = await self.chain.ainvoke({
                        "input": final_input,
                        "chat_history": chat_history
                    })
                    response = final_response
            
            # 保存对话到内存
            if session_id:
                await self.memory_manager.add_message(session_id, HumanMessage(content=message))
                await self.memory_manager.add_message(session_id, AIMessage(content=response))
            
            return AgentResponse(
                success=True,
                content=response,
                tool_calls=tool_calls,
                metadata={
                    "processing_mode": "adaptive",
                    "agent_type": "adaptive",
                    "model": self.model_config["model"],
                    "tools_used": len(tool_calls)
                }
            )
            
        except Exception as e:
            logger.error(f"Prompt tool processing failed: {e}")
            raise
    
    def _should_call_tools(self, response: str) -> bool:
        """判断是否需要调用工具"""
        return "TOOL_CALL:" in response
    
    def _extract_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """从响应中提取工具调用 - 支持JSON格式"""
        import json
        import re

        tool_calls = []

        try:
            # 提取JSON格式的工具调用
            tool_call_pattern = r'TOOL_CALL:\s*({[^}]+})'
            matches = re.findall(tool_call_pattern, response)

            for match in matches:
                try:
                    tool_call_data = json.loads(match)
                    tool_calls.append({
                        "tool": tool_call_data.get("tool", ""),
                        "input": tool_call_data.get("input", ""),
                        "reasoning": "JSON格式工具调用"
                    })
                except json.JSONDecodeError:
                    continue

            # 如果没有找到JSON格式，尝试旧格式
            if not tool_calls:
                lines = response.split('\n')
                current_tool_call = {}

                for line in lines:
                    line = line.strip()
                    if line.startswith("TOOL_CALL:"):
                        if current_tool_call:
                            tool_calls.append(current_tool_call)
                        current_tool_call = {"tool": line.replace("TOOL_CALL:", "").strip()}
                    elif line.startswith("PARAMETERS:"):
                        try:
                            params_str = line.replace("PARAMETERS:", "").strip()
                            current_tool_call["input"] = json.loads(params_str)
                        except:
                            current_tool_call["input"] = {}
                    elif line.startswith("REASONING:"):
                        current_tool_call["reasoning"] = line.replace("REASONING:", "").strip()

                if current_tool_call:
                    tool_calls.append(current_tool_call)

        except Exception as e:
            logger.error(f"Failed to extract tool calls: {e}")

        return tool_calls
    
    async def _execute_tool_call(self, tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具调用"""
        try:
            tool_name = tool_call.get("tool", "")
            tool_input = tool_call.get("input", {})
            
            if tool_name in self.tool_manager.tools:
                tool = self.tool_manager.tools[tool_name]
                result = await tool.execute(**tool_input)
                return {
                    "success": result.get("success", True),
                    "result": result.get("result", "")
                }
            else:
                return {
                    "success": False,
                    "result": f"工具 {tool_name} 不存在"
                }
        except Exception as e:
            return {
                "success": False,
                "result": f"工具执行失败: {str(e)}"
            }
    
    async def _get_chat_history(self, session_id: str = None) -> List:
        """获取聊天历史"""
        if not session_id:
            return []
        
        try:
            messages = await self.memory_manager.get_messages(session_id)
            history = []
            
            for msg in messages[-10:]:  # 只取最近10条消息
                if msg.role == "human":
                    history.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    history.append(AIMessage(content=msg.content))
            
            return history
        except Exception as e:
            logger.error(f"Failed to get chat history: {e}")
            return []
    
    async def get_info(self) -> Dict[str, Any]:
        """获取 Agent 信息"""
        return {
            "type": "adaptive",
            "name": "Adaptive Agent",
            "description": "智能自适应Agent，根据任务自动选择最佳处理策略",
            "features": [
                "自动任务分析",
                "智能模式切换",
                "工具调用优化",
                "流式输出支持",
                "开发者模式信息"
            ],
            "model": self.model_config.get("model", "unknown") if self.model_config else "unknown",
            "tools_count": len(self.tool_manager.tools) if self.tool_manager else 0,
            "supports_native_tools": self.tool_manager.supports_native_tools if self.tool_manager else False,
            "current_mode": self.current_mode,
            "initialized": self._initialized
        }

    # 实现抽象方法
    def add_tool(self, tool) -> bool:
        """添加工具"""
        if self.tool_manager:
            self.tool_manager.add_tool(tool)
            return True
        return False

    def remove_tool(self, tool_name: str) -> bool:
        """移除工具"""
        if self.tool_manager and tool_name in self.tool_manager.tools:
            del self.tool_manager.tools[tool_name]
            return True
        return False

    def list_tools(self) -> List[str]:
        """列出所有工具"""
        if self.tool_manager:
            return list(self.tool_manager.tools.keys())
        return []

    async def chat_stream(self, message: str, session_id: str = None, **kwargs):
        """流式对话"""
        try:
            # 先调用普通chat方法获取完整响应
            response = await self.chat(message, session_id, **kwargs)

            # 模拟流式输出
            content = response.content
            chunk_size = 10  # 每次发送10个字符

            for i in range(0, len(content), chunk_size):
                chunk = content[i:i+chunk_size]
                yield {
                    "success": True,
                    "content": chunk,
                    "done": i + chunk_size >= len(content),
                    "thinking_process": response.thinking_process if i == 0 else "",
                    "tool_calls": response.tool_calls if i == 0 else []
                }
                await asyncio.sleep(0.05)  # 模拟网络延迟

        except Exception as e:
            yield {
                "success": False,
                "content": f"流式输出错误: {str(e)}",
                "done": True,
                "error": str(e)
            }

    async def get_memory(self, session_id: str) -> List:
        """获取记忆"""
        return await self._get_chat_history(session_id)

    async def clear_memory(self, session_id: str) -> bool:
        """清除记忆"""
        if self.memory_manager:
            try:
                # 这里需要实现清除特定会话的记忆
                return True
            except:
                return False
        
    def _collect_dev_info(self, message: str, response: str, tool_calls: list) -> dict:
        """收集开发者模式信息"""
        return {
            "messages": [
                {"type": "HumanMessage", "content": message, "timestamp": "now"},
                {"type": "AIMessage", "content": response, "timestamp": "now"}
            ],
            "function_calls": [
                "chat", "_process_with_prompt_tools", "_extract_tool_calls"
            ],
            "tool_interactions": [
                {
                    "tool": tc.get("tool", "unknown"),
                    "input": tc.get("input", {}),
                    "output": tc.get("result", ""),
                    "success": tc.get("success", True)
                } for tc in tool_calls
            ],
            "processing_steps": [
                "接收用户消息",
                "分析任务复杂度",
                "选择处理策略",
                "执行工具调用" if tool_calls else "直接生成回复",
                "返回最终结果"
            ]
        }


# 为了向后兼容，保留原名称
ImprovedChainAgent = AdaptiveAgent
