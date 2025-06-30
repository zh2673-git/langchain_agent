"""
LangChain核心Agent实现
完全基于LangChain官方源码和最佳实践
"""

import asyncio
from typing import Dict, Any, List, Optional, AsyncIterator, Union, Sequence
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable, RunnablePassthrough, RunnableLambda
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama
import json
import re

from ..base.agent_base import AgentBase
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LangChainCoreAgent(AgentBase):
    """
    LangChain核心Agent - 完全基于LangChain官方实现
    
    特点：
    1. 使用LangChain原生@tool装饰器工具
    2. 完全遵循LangChain最佳实践
    3. 支持流式输出和工具调用
    4. 智能适配不同模型的工具支持能力
    """
    
    def __init__(self, provider: str = "ollama", model: str = "qwen2.5:7b"):
        super().__init__(name="langchain_core")
        self.provider = provider
        self.model = model
        self.model_name = f"{provider}:{model}"
        
        # LangChain组件
        self.llm = None
        self.tools: List = []
        self.memory = None
        self.initialized = False
        
        # Agent组件
        self.agent: Optional[Runnable] = None
        self.agent_executor: Optional[AgentExecutor] = None
        self.chain: Optional[Runnable] = None
        
        # 回调处理器
        self.callbacks = []
        
        logger.info(f"LangChainCoreAgent created for {self.model_name}")
    
    async def initialize(self) -> bool:
        """初始化Agent - 按照LangChain标准流程"""
        try:
            # 1. 初始化LLM
            await self._initialize_llm()
            
            # 2. 加载工具
            await self._load_tools()
            
            # 3. 构建处理链
            await self._build_processing_chain()
            
            self.initialized = True
            logger.info("LangChainCoreAgent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LangChainCoreAgent: {e}")
            return False
    
    async def _initialize_llm(self):
        """初始化语言模型"""
        if self.provider == "ollama":
            self.llm = ChatOllama(
                model=self.model,
                temperature=0.7,
                num_predict=2048,
                top_k=40,
                top_p=0.9,
                repeat_penalty=1.1
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
        
        # 检查模型工具支持
        supports_tools = self._check_tool_support()
        logger.info(f"Model supports tools: {supports_tools}")
    
    def _check_tool_support(self) -> bool:
        """检查模型是否支持原生工具调用"""
        # 大部分开源模型不支持原生工具调用，使用提示词方式
        return False
    
    async def _load_tools(self):
        """加载工具 - 包含内置、自定义和MCP工具"""
        # 1. LangChain内置工具（原langchain_native）
        from ..tools.builtin.calculator_native import calculator, math_help
        from ..tools.builtin.file_native import list_files, read_file, get_file_info
        from ..tools.builtin.search_native import web_search, local_search

        # 2. LangChain社区内置工具（原langchain_builtin）
        from ..tools.builtin.python_repl_tool import python_repl_tool, safe_python_exec, python_calculator
        from ..tools.builtin.shell_tool import shell_tool, safe_shell_exec, system_info
        from ..tools.builtin.database_tools import sql_query, list_tables, describe_table

        # 3. 自定义工具
        from ..tools.custom.demo_custom_tool import demo_custom_tool, weather_tool, random_quote_tool
        from ..tools.custom.text_processing_tool import text_analyzer_tool, text_formatter_tool, text_search_replace_tool

        # 4. MCP工具
        from ..tools.mcp.mcp_base import mcp_placeholder_tool

        # 组合所有工具
        self.tools = [
            # 内置工具（LangChain官方）
            calculator,
            list_files,
            read_file,
            get_file_info,
            web_search,
            local_search,
            python_repl_tool,
            safe_python_exec,
            python_calculator,
            safe_shell_exec,
            system_info,
            sql_query,
            list_tables,
            describe_table,

            # 自定义工具（用户编写）
            demo_custom_tool,
            weather_tool,
            random_quote_tool,
            text_analyzer_tool,
            text_formatter_tool,
            text_search_replace_tool,

            # MCP工具
            mcp_placeholder_tool
        ]

        logger.info(f"Loaded {len(self.tools)} tools (builtin + custom + mcp)")
    

    
    async def _build_processing_chain(self):
        """构建处理链 - 根据模型能力选择策略"""
        supports_tools = self._check_tool_support()
        
        if supports_tools:
            # 使用原生工具调用
            await self._build_native_tool_chain()
        else:
            # 使用提示词工具调用
            await self._build_prompt_tool_chain()
    
    async def _build_native_tool_chain(self):
        """构建原生工具调用链"""
        # 创建系统提示
        system_prompt = """你是一个智能助手，可以使用提供的工具来帮助用户。
        
请根据用户的问题，选择合适的工具来获取信息或执行操作。
如果需要使用工具，请直接调用相应的工具函数。
"""
        
        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # 创建Agent
        self.agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        self.agent_executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)
        
        logger.info("Native tool calling chain built successfully")
    
    async def _build_prompt_tool_chain(self):
        """构建基于提示词的工具调用链"""
        # 创建工具描述
        tools_description = "\n".join([
            f"- {tool.name}: {tool.description}" 
            for tool in self.tools
        ])
        
        system_prompt = f"""你是一个智能助手，可以使用以下工具来帮助用户：

{tools_description}

当你需要使用工具时，请按照以下格式输出：
TOOL_CALL: {{{{\"tool\": \"工具名称\", \"input\": \"输入参数\"}}}}

例如：
- 计算数学问题：TOOL_CALL: {{{{\"tool\": \"calculator\", \"input\": \"2 + 3 * 4\"}}}}
- 列出桌面文件：TOOL_CALL: {{{{\"tool\": \"list_files\", \"input\": \"desktop\"}}}}
- 搜索信息：TOOL_CALL: {{{{\"tool\": \"web_search\", \"input\": \"Python编程教程\"}}}}

请根据用户的问题，选择合适的工具并提供有用的回答。
"""
        
        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        # 构建链
        self.chain = (
            RunnablePassthrough.assign(
                chat_history=lambda x: self._get_chat_history()
            )
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        logger.info("Prompt-based tool calling chain built successfully")
    
    async def _build_conversation_chain(self):
        """构建对话链 - 不使用工具的简单对话"""
        system_prompt = """你是一个智能助手，请根据用户的问题提供有用的回答。
        
请保持回答的准确性和有用性。如果不确定某些信息，请诚实地说明。
"""
        
        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        # 构建链 - 使用LangChain的Runnable接口
        self.chain = (
            RunnablePassthrough.assign(
                chat_history=lambda x: self._get_chat_history()
            )
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        logger.info("Conversation chain built successfully")
    
    def _get_chat_history(self) -> List[BaseMessage]:
        """获取聊天历史 - 转换为LangChain消息格式"""
        # 这里可以从内存管理器获取历史
        return []
    
    async def _handle_prompt_tool_call(self, response_content: str) -> tuple[List[Dict], str]:
        """处理基于提示词的工具调用"""
        tool_calls = []
        final_response = response_content
        
        try:
            # 使用正则表达式查找工具调用
            tool_call_pattern = r'TOOL_CALL:\s*({[^}]+})'
            matches = re.findall(tool_call_pattern, response_content)

            for match in matches:
                try:
                    # 尝试多种JSON解析策略
                    tool_call_data = None

                    # 策略1: 直接解析
                    try:
                        tool_call_data = json.loads(match)
                    except json.JSONDecodeError:
                        pass

                    # 策略2: 修复常见格式问题
                    if tool_call_data is None:
                        try:
                            fixed_json = match
                            # 修复缺少引号的问题
                            fixed_json = re.sub(r'(\w+):', r'"\1":', fixed_json)
                            # 修复已经有引号但格式不对的问题
                            fixed_json = re.sub(r'""(\w+)":', r'"\1":', fixed_json)
                            tool_call_data = json.loads(fixed_json)
                        except json.JSONDecodeError:
                            pass

                    # 策略2.5: 处理不完整的JSON（缺少结束括号）
                    if tool_call_data is None and not match.strip().endswith('}'):
                        try:
                            # 计算需要的结束括号数量
                            open_braces = match.count('{')
                            close_braces = match.count('}')
                            missing_braces = open_braces - close_braces

                            if missing_braces > 0:
                                fixed_match = match + '}' * missing_braces
                                tool_call_data = json.loads(fixed_match)
                        except json.JSONDecodeError:
                            pass

                    # 策略3: 处理嵌套JSON对象和复杂字符串
                    if tool_call_data is None:
                        try:
                            # 尝试提取工具名称
                            tool_match = re.search(r'"tool":\s*"([^"]+)"', match)
                            if tool_match:
                                tool_name_extracted = tool_match.group(1)

                                # 尝试提取input内容（支持多种格式）
                                input_content = None

                                # 格式1: JSON对象 {"input": {...}}
                                input_json_match = re.search(r'"input":\s*({[^}]*})', match)
                                if input_json_match:
                                    try:
                                        input_content = json.loads(input_json_match.group(1))
                                    except json.JSONDecodeError:
                                        input_content = input_json_match.group(1)

                                # 格式2: 字符串 {"input": "..."}
                                if input_content is None:
                                    input_str_match = re.search(r'"input":\s*"([^"]*)"', match)
                                    if input_str_match:
                                        input_content = input_str_match.group(1)

                                # 格式3: 复杂字符串（可能包含换行和特殊字符）
                                if input_content is None:
                                    input_complex_match = re.search(r'"input":\s*\'([^\']*?)\'', match, re.DOTALL)
                                    if input_complex_match:
                                        input_content = input_complex_match.group(1)

                                # 格式4: 没有引号的复杂内容
                                if input_content is None:
                                    input_raw_match = re.search(r'"input":\s*([^}]+)', match)
                                    if input_raw_match:
                                        input_content = input_raw_match.group(1).strip()
                                        # 移除末尾的逗号或其他符号
                                        input_content = re.sub(r'[,\s]*$', '', input_content)

                                if input_content is not None:
                                    tool_call_data = {
                                        "tool": tool_name_extracted,
                                        "input": input_content
                                    }
                        except (json.JSONDecodeError, AttributeError):
                            pass

                    # 策略4: 使用正则表达式提取简单字符串
                    if tool_call_data is None:
                        tool_match = re.search(r'"tool":\s*"([^"]+)"', match)
                        input_match = re.search(r'"input":\s*"([^"]+)"', match)
                        if tool_match and input_match:
                            tool_call_data = {
                                "tool": tool_match.group(1),
                                "input": input_match.group(1)
                            }

                    if tool_call_data is None:
                        logger.error(f"Failed to parse tool call: {match}")
                        continue
                    tool_name = tool_call_data.get("tool")
                    tool_input = tool_call_data.get("input")

                    # 查找对应的工具
                    tool = None
                    for t in self.tools:
                        if t.name == tool_name:
                            tool = t
                            break

                    if tool:
                        # 执行工具
                        try:
                            # 调试：打印工具调用信息
                            logger.info(f"Tool call debug - tool: {tool_name}, input: {tool_input}, type: {type(tool_input)}")
                            
                            # 解析工具输入参数 - 适配所有类型的工具
                            if isinstance(tool_input, str):
                                # 根据工具名称映射参数
                                if tool_name == "list_files":
                                    tool_args = {"path": tool_input}
                                elif tool_name == "read_file":
                                    tool_args = {"file_path": tool_input}
                                elif tool_name == "get_file_info":
                                    tool_args = {"file_path": tool_input}
                                elif tool_name == "calculator":
                                    tool_args = {"expression": tool_input}
                                elif tool_name in ["web_search", "local_search"]:
                                    tool_args = {"query": tool_input}
                                elif tool_name in ["python_repl_tool", "safe_python_exec"]:
                                    tool_args = {"code": tool_input}
                                elif tool_name == "python_calculator":
                                    tool_args = {"expression": tool_input}
                                elif tool_name in ["shell_tool", "safe_shell_exec"]:
                                    tool_args = {"command": tool_input}
                                elif tool_name == "sql_query":
                                    tool_args = {"query": tool_input}
                                elif tool_name == "describe_table":
                                    tool_args = {"table_name": tool_input}
                                elif tool_name == "mcp_placeholder_tool":
                                    tool_args = {"action": tool_input}
                                elif tool_name == "demo_custom_tool":
                                    tool_args = {"message": tool_input}
                                elif tool_name == "weather_tool":
                                    tool_args = {"city": tool_input}
                                elif tool_name == "random_quote_tool":
                                    tool_args = {"category": tool_input}
                                elif tool_name == "text_analyzer_tool":
                                    tool_args = {"text": tool_input}
                                elif tool_name == "text_formatter_tool":
                                    # 需要解析格式类型
                                    parts = tool_input.split(',', 1)
                                    if len(parts) >= 2:
                                        tool_args = {"text": parts[1].strip(), "format_type": parts[0].strip()}
                                    else:
                                        tool_args = {"text": tool_input, "format_type": "clean"}
                                elif tool_name == "text_search_replace_tool":
                                    # 需要解析搜索和替换参数
                                    parts = tool_input.split(',', 2)
                                    if len(parts) >= 3:
                                        tool_args = {"text": parts[0].strip(), "search_pattern": parts[1].strip(), "replacement": parts[2].strip()}
                                    else:
                                        tool_args = {"text": tool_input, "search_pattern": "", "replacement": ""}
                                else:
                                    # 其他工具：尝试作为第一个参数
                                    tool_args = {"input": tool_input}
                            else:
                                # 如果已经是字典格式，需要映射参数名
                                if isinstance(tool_input, dict):
                                    # 处理嵌套的input字典
                                    if "input" in tool_input and isinstance(tool_input["input"], dict):
                                        # 嵌套格式：{"input": {"path": "desktop"}}
                                        nested_input = tool_input["input"]
                                        if tool_name == "list_files" and "path" in nested_input:
                                            tool_args = {"path": nested_input["path"]}
                                        else:
                                            tool_args = nested_input
                                    elif "input" in tool_input:
                                        # 简单格式：{"input": "desktop"}
                                        if tool_name == "list_files":
                                            tool_args = {"path": tool_input["input"]}
                                        elif tool_name == "calculator":
                                            tool_args = {"expression": tool_input["input"]}
                                        else:
                                            tool_args = {"input": tool_input["input"]}
                                    else:
                                        tool_args = tool_input
                                else:
                                    tool_args = {"input": tool_input}
                            
                            # 调用工具 - 优先使用异步调用
                            logger.info(f"Tool args debug - tool: {tool_name}, args: {tool_args}")
                            try:
                                if hasattr(tool, 'ainvoke'):
                                    result = await tool.ainvoke(tool_args)
                                elif hasattr(tool, 'invoke'):
                                    result = tool.invoke(tool_args)
                                elif hasattr(tool, '_arun'):
                                    result = await tool._arun(tool_args)
                                elif hasattr(tool, '_run'):
                                    result = tool._run(tool_args)
                                else:
                                    result = f"工具 {tool_name} 不支持调用"
                            except Exception as invoke_error:
                                # 如果同步调用失败，尝试异步调用
                                if "sync invocation" in str(invoke_error) and hasattr(tool, 'ainvoke'):
                                    result = await tool.ainvoke(tool_args)
                                else:
                                    raise invoke_error
                            
                            # 记录工具调用
                            tool_calls.append({
                                "tool": tool_name,
                                "input": tool_input,
                                "result": str(result),
                                "success": True
                            })
                            
                            # 替换工具调用为结果
                            tool_result = f"[使用工具 {tool_name}] {result}"
                            final_response = final_response.replace(f"TOOL_CALL: {match}", tool_result)
                            
                        except Exception as e:
                            logger.error(f"Tool execution failed: {e}")
                            
                            # 记录失败的工具调用
                            tool_calls.append({
                                "tool": tool_name,
                                "input": tool_input,
                                "result": None,
                                "success": False,
                                "error": str(e)
                            })
                            
                            # 替换为错误信息
                            error_text = f"[工具 {tool_name} 执行失败: {str(e)}]"
                            final_response = final_response.replace(f"TOOL_CALL: {match}", error_text)
                    else:
                        logger.warning(f"Tool not found: {tool_name}")

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse tool call JSON: {e}")

        except Exception as e:
            logger.error(f"Failed to handle prompt tool call: {e}")

        return tool_calls, final_response
    
    async def chat(self, message: str, session_id: str = None, **kwargs) -> Dict[str, Any]:
        """聊天方法 - 完全按照LangChain标准实现"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # 准备输入
            input_data = {"input": message}
            
            # 执行链
            if self.agent_executor:
                # 使用Agent执行器
                response = await self.agent_executor.ainvoke(input_data)
                content = response.get("output", "")
                tool_calls = []
            elif self.chain:
                # 使用自定义链
                response = await self.chain.ainvoke(input_data)
                content = response if isinstance(response, str) else str(response)
                
                # 处理工具调用
                tool_calls, content = await self._handle_prompt_tool_call(content)
            else:
                return {
                    "success": False,
                    "content": "Agent not properly initialized"
                }
            
            return {
                "success": True,
                "content": content,
                "tool_calls": tool_calls,
                "model": self.model_name,
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return {
                "success": False,
                "content": f"处理消息时出错: {str(e)}"
            }
    
    async def chat_stream(self, message: str, session_id: str = None, **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """流式聊天 - 完全按照LangChain流式接口实现"""
        try:
            if not self.initialized:
                await self.initialize()
            
            # 准备输入
            input_data = {"input": message}
            
            if self.chain:
                # 使用流式输出
                full_response = ""
                async for chunk in self.chain.astream(input_data):
                    if isinstance(chunk, str):
                        full_response += chunk
                        yield {
                            "success": True,
                            "content": chunk,
                            "is_complete": False,
                            "model": self.model_name
                        }
                
                # 处理工具调用
                tool_calls, final_content = await self._handle_prompt_tool_call(full_response)
                
                # 发送最终结果
                yield {
                    "success": True,
                    "content": final_content,
                    "is_complete": True,
                    "tool_calls": tool_calls,
                    "model": self.model_name,
                    "session_id": session_id
                }
            else:
                # 回退到非流式
                result = await self.chat(message, session_id, **kwargs)
                yield result
                
        except Exception as e:
            logger.error(f"Stream chat failed: {e}")
            yield {
                "success": False,
                "content": f"流式聊天出错: {str(e)}",
                "is_complete": True
            }
    
    async def get_info(self) -> Dict[str, Any]:
        """获取Agent信息"""
        return {
            "type": "langchain_core",
            "provider": self.provider,
            "model": self.model,
            "initialized": self.initialized,
            "supports_tools": len(self.tools) > 0,
            "tools_count": len(self.tools),
            "memory_enabled": self.memory is not None,
            "memory_size": 0 if not self.memory else getattr(self.memory, 'size', 0)
        }
    
    async def clear_memory(self, session_id: str = None) -> bool:
        """清除记忆"""
        if self.memory:
            return await self.memory.clear(session_id)
        return True
    
    async def get_memory_info(self, session_id: str = None) -> Dict[str, Any]:
        """获取记忆信息"""
        if self.memory:
            return await self.memory.get_info(session_id)
        return {"enabled": False, "size": 0}

    # 实现抽象方法
    async def add_tool(self, tool_name: str, tool_config: Dict[str, Any]) -> bool:
        """添加工具"""
        # LangChain Core Agent 使用固定的工具集
        return False

    async def remove_tool(self, tool_name: str) -> bool:
        """移除工具"""
        # LangChain Core Agent 使用固定的工具集
        return False

    async def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "type": "langchain_native"
            }
            for tool in self.tools
        ]

    async def get_memory(self, session_id: str = None) -> Dict[str, Any]:
        """获取内存信息"""
        return await self.get_memory_info(session_id)
