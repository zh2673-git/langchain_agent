"""
Agent API 接口
提供统一的 Agent 调用接口

支持三种LangChain实现方式：
1. Chain方式：使用Runnable接口组合
2. Agent方式：使用create_tool_calling_agent
3. LangGraph方式：使用LangGraph状态图
"""
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime

from ..agents.chain_agent import ChainAgent
from ..agents.agent_agent import AgentAgent
from ..agents.langgraph_agent import LangGraphAgent
from ..config import config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AgentAPI:
    """Agent API 类 - 统一三种LangChain实现方式"""

    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.current_agent: Optional[Any] = None
        self.current_agent_type: Optional[str] = None
        self.current_session_id: Optional[str] = None
        self.initialized = False

    async def initialize(self) -> bool:
        """初始化 API"""
        try:
            # 初始化三种LangChain实现方式
            agent_classes = {
                "chain": ChainAgent,        # 🔗 Chain方式：使用Runnable接口组合
                "agent": AgentAgent,        # 🤖 Agent方式：使用create_tool_calling_agent
                "langgraph": LangGraphAgent # 📊 LangGraph方式：使用状态图
            }

            for agent_type, agent_class in agent_classes.items():
                try:
                    # 创建Agent实例
                    agent = agent_class()

                    # 异步初始化
                    if await agent.initialize():
                        self.agents[agent_type] = agent
                        logger.info(f"✅ Initialized {agent_type} agent successfully")
                    else:
                        logger.error(f"❌ Failed to initialize {agent_type} agent")
                except Exception as e:
                    logger.error(f"Error initializing {agent_type} agent: {e}")
            
            # 设置默认 Agent - 优先使用Chain方式
            if "chain" in self.agents:
                self.current_agent = self.agents["chain"]
                self.current_agent_type = "chain"
            elif "agent" in self.agents:
                self.current_agent = self.agents["agent"]
                self.current_agent_type = "agent"
            elif "langgraph" in self.agents:
                self.current_agent = self.agents["langgraph"]
                self.current_agent_type = "langgraph"
            
            self.initialized = True
            logger.info("Agent API initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Agent API: {e}")
            return False
    
    def get_available_agents(self) -> List[str]:
        """获取可用的 Agent 列表"""
        return list(self.agents.keys())
    
    def set_current_agent(self, agent_type: str) -> bool:
        """设置当前使用的 Agent"""
        if agent_type in self.agents:
            self.current_agent = self.agents[agent_type]
            self.current_agent_type = agent_type
            logger.info(f"Switched to {agent_type} agent")
            return True
        return False

    # 别名方法，保持向后兼容
    def switch_agent(self, agent_type: str) -> bool:
        """切换Agent - set_current_agent的别名"""
        return self.set_current_agent(agent_type)

    async def reinitialize_current_agent(self) -> bool:
        """重新初始化当前Agent（用于模型配置更新后）"""
        if not self.current_agent or not self.current_agent_type:
            return False

        try:
            logger.info(f"Reinitializing {self.current_agent_type} agent with new model config")

            # 重新初始化当前Agent
            success = await self.current_agent.initialize()
            if success:
                logger.info(f"Successfully reinitialized {self.current_agent_type} agent")
                return True
            else:
                logger.error(f"Failed to reinitialize {self.current_agent_type} agent")
                return False

        except Exception as e:
            logger.error(f"Error reinitializing {self.current_agent_type} agent: {e}")
            return False

    async def reinitialize_all_agents(self) -> bool:
        """重新初始化所有Agent（用于全局配置更新后）"""
        try:
            logger.info("Reinitializing all agents with new model config")

            success_count = 0
            for agent_type, agent in self.agents.items():
                try:
                    if await agent.initialize():
                        success_count += 1
                        logger.info(f"Successfully reinitialized {agent_type} agent")
                    else:
                        logger.error(f"Failed to reinitialize {agent_type} agent")
                except Exception as e:
                    logger.error(f"Error reinitializing {agent_type} agent: {e}")

            logger.info(f"Reinitialized {success_count}/{len(self.agents)} agents successfully")
            return success_count > 0

        except Exception as e:
            logger.error(f"Error reinitializing agents: {e}")
            return False
    
    def get_current_agent_type(self) -> Optional[str]:
        """获取当前 Agent 类型"""
        if not self.current_agent:
            return None
        
        for agent_type, agent in self.agents.items():
            if agent == self.current_agent:
                return agent_type
        return None
    
    async def chat(self, message: str, session_id: str = None) -> Dict[str, Any]:
        """与当前 Agent 对话"""
        if not self.current_agent:
            return {
                "success": False,
                "error": "No agent selected",
                "content": "请先选择一个 Agent"
            }
        
        try:
            # 使用提供的 session_id 或当前会话 ID
            use_session_id = session_id or self.current_session_id
            
            response = await self.current_agent.chat(message, use_session_id)

            # LangChain核心Agent返回字典格式，自适应Agent返回AgentResponse对象
            if isinstance(response, dict):
                # LangChain核心Agent的响应格式
                result = response.copy()
                result["session_id"] = use_session_id
                result["agent_type"] = self.get_current_agent_type()
                return result
            else:
                # 兼容旧的AgentResponse格式
                # 如果没有提供 session_id，更新当前会话 ID
                if not session_id and hasattr(response, 'metadata') and response.metadata.get("session_id"):
                    self.current_session_id = response.metadata["session_id"]

                return {
                    "success": getattr(response, 'success', True),
                    "content": response.content or "AI响应为空",
                    "tool_calls": response.tool_calls or [],
                    "thinking_process": getattr(response, 'thinking_process', ''),
                    "execution_steps": getattr(response, 'execution_steps', []),
                    "metadata": getattr(response, 'metadata', {}),
                    "session_id": getattr(response, 'metadata', {}).get("session_id", use_session_id) if hasattr(response, 'metadata') else use_session_id,
                    "agent_type": self.get_current_agent_type()
                }
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": f"对话出现错误: {str(e)}"
            }
    
    async def chat_stream(self, message: str, session_id: str = None) -> AsyncGenerator[Dict[str, Any], None]:
        """流式对话"""
        if not self.current_agent:
            yield {
                "success": False,
                "error": "No agent selected",
                "content": "请先选择一个 Agent",
                "done": True
            }
            return
        
        try:
            use_session_id = session_id or self.current_session_id

            async for chunk in self.current_agent.chat_stream(message, use_session_id):
                # LangChain核心Agent返回字典格式
                if isinstance(chunk, dict):
                    # 直接传递LangChain Agent的响应格式
                    chunk["session_id"] = use_session_id
                    chunk["agent_type"] = self.get_current_agent_type()
                    yield chunk
                else:
                    # 兼容旧格式（字符串）
                    yield {
                        "success": True,
                        "content": str(chunk),
                        "done": False,
                        "session_id": use_session_id,
                        "agent_type": self.get_current_agent_type()
                    }

            # 如果最后一个chunk没有done=True，发送结束标记
            yield {
                "success": True,
                "content": "",
                "done": True,
                "session_id": use_session_id,
                "agent_type": self.get_current_agent_type()
            }
            
        except Exception as e:
            logger.error(f"Stream chat error: {e}")
            yield {
                "success": False,
                "error": str(e),
                "content": f"流式对话出现错误: {str(e)}",
                "done": True
            }
    
    async def get_agent_info(self, agent_type: str = None) -> Dict[str, Any]:
        """获取 Agent 信息"""
        if agent_type and agent_type in self.agents:
            agent = self.agents[agent_type]
        elif self.current_agent:
            agent = self.current_agent
        else:
            return {"error": "No agent selected"}

        info = await agent.get_info()
        info["agent_type"] = agent_type or self.get_current_agent_type()
        return info
    
    def list_tools(self, agent_type: str = None) -> List[str]:
        """列出工具"""
        if agent_type and agent_type in self.agents:
            agent = self.agents[agent_type]
        elif self.current_agent:
            agent = self.current_agent
        else:
            return []
        
        tools = agent.list_tools()
        return tools

    def get_tools_detail(self) -> Dict[str, Any]:
        """获取工具详细信息 - 支持新的LangChain工具架构"""
        import inspect

        tools_detail = {
            "builtin_tools": [],      # LangChain官方内置工具
            "custom_tools": [],       # 用户自定义工具
            "mcp_tools": [],          # MCP协议工具
            "total_count": 0
        }

        # 获取当前Agent的工具
        current_agent = self.agents.get(self.current_agent_type)
        if not current_agent:
            return tools_detail

        # 获取Agent的工具列表
        if hasattr(current_agent, 'tools') and current_agent.tools:
            for tool in current_agent.tools:
                try:
                    # 获取工具基本信息
                    tool_name = getattr(tool, 'name', str(tool))
                    tool_description = getattr(tool, 'description', '无描述')

                    # 获取工具源代码
                    source_code = ""
                    try:
                        if hasattr(tool, 'func'):
                            # LangChain @tool装饰器工具
                            source_code = inspect.getsource(tool.func)
                        elif hasattr(tool, '_run'):
                            source_code = inspect.getsource(tool._run)
                        else:
                            source_code = f"# LangChain工具: {tool_name}"
                    except Exception as e:
                        source_code = f"# 无法获取源代码: {str(e)}"

                    # 获取参数信息
                    parameters = []
                    if hasattr(tool, 'args_schema') and tool.args_schema:
                        try:
                            schema_fields = tool.args_schema.__fields__
                            for field_name, field_info in schema_fields.items():
                                parameters.append({
                                    "name": field_name,
                                    "type": str(field_info.type_),
                                    "description": field_info.field_info.description or "",
                                    "required": field_info.required,
                                    "default": field_info.default if field_info.default != ... else None
                                })
                        except Exception as e:
                            parameters = [{"name": "input", "type": "str", "description": "工具输入", "required": True, "default": None}]

                    tool_info = {
                        "name": tool_name,
                        "description": tool_description,
                        "type": self._classify_tool_type(tool_name, tool),
                        "source_code": source_code,
                        "class_name": tool.__class__.__name__,
                        "module_path": tool.__class__.__module__,
                        "parameters": parameters
                    }

                    # 根据工具类型分类
                    tool_type = self._classify_tool_type(tool_name, tool)
                    if tool_type == "mcp":
                        tools_detail["mcp_tools"].append(tool_info)
                    elif tool_type == "custom":
                        tools_detail["custom_tools"].append(tool_info)
                    else:
                        tools_detail["builtin_tools"].append(tool_info)

                except Exception as e:
                    # 如果处理某个工具失败，记录错误但继续处理其他工具
                    print(f"处理工具时出错: {e}")
                    continue

        # 更新总数
        tools_detail["total_count"] = (
            len(tools_detail["builtin_tools"]) +
            len(tools_detail["custom_tools"]) +
            len(tools_detail["mcp_tools"])
        )

        return tools_detail

    def _classify_tool_type(self, tool_name: str, tool) -> str:
        """分类工具类型"""
        module_path = tool.__class__.__module__

        if "mcp" in module_path or tool_name.startswith("mcp_"):
            return "mcp"
        elif "custom" in module_path or tool_name in [
            "demo_custom_tool", "weather_tool", "random_quote_tool",
            "text_analyzer_tool", "text_formatter_tool", "text_search_replace_tool"
        ]:
            return "custom"
        else:
            return "builtin"

    def get_tool_config(self, tool_name: str = None) -> Dict[str, Any]:
        """获取工具配置"""
        import json
        import os

        config_path = os.path.join(os.path.dirname(__file__), "tools", "tools_config.json")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            if tool_name:
                return config.get("tool_settings", {}).get(tool_name, {})
            else:
                return config.get("tool_settings", {})

        except Exception as e:
            logger.error(f"Failed to get tool config: {e}")
            return {}

    def update_tool_config(self, tool_name: str, settings: Dict[str, Any]) -> bool:
        """更新工具配置"""
        import json
        import os

        config_path = os.path.join(os.path.dirname(__file__), "tools", "tools_config.json")

        try:
            # 读取现有配置
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {
                    "tool_directories": [
                        "backend.tools.builtin",
                        "backend.tools.custom"
                    ],
                    "disabled_tools": [],
                    "tool_settings": {}
                }

            # 更新工具设置
            if "tool_settings" not in config:
                config["tool_settings"] = {}

            config["tool_settings"][tool_name] = settings

            # 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logger.info(f"Updated tool config for {tool_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update tool config: {e}")
            return False

    def test_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """测试工具执行"""
        from .base.tool_base import tool_registry
        import asyncio

        try:
            # 获取工具
            tool = tool_registry.get_tool(tool_name)
            if not tool:
                return {
                    "success": False,
                    "error": f"工具 {tool_name} 不存在"
                }

            # 执行工具
            def run_tool():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(tool.execute(**parameters))
                finally:
                    loop.close()

            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_tool)
                result = future.result(timeout=30)

            return {
                "success": result.success,
                "result": result.result if result.success else None,
                "error": result.error if not result.success else None,
                "tool_name": tool_name,
                "parameters": parameters
            }

        except Exception as e:
            logger.error(f"Tool test failed: {e}")
            return {
                "success": False,
                "error": f"工具测试失败: {str(e)}",
                "tool_name": tool_name,
                "parameters": parameters
            }

    def get_session_list(self) -> List[Dict[str, Any]]:
        """获取会话列表"""
        try:
            # 获取当前Agent的内存管理器
            current_agent = self.agents.get(self.current_agent_type)
            if current_agent and hasattr(current_agent, 'memory_manager'):
                return current_agent.memory_manager.get_session_list()
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to get session list: {e}")
            return []

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话历史"""
        try:
            current_agent = self.agents.get(self.current_agent_type)
            if current_agent and hasattr(current_agent, 'memory_manager'):
                return current_agent.memory_manager.get_session_history(session_id)
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to get session history: {e}")
            return []

    def restore_session(self, session_id: str) -> bool:
        """恢复会话"""
        try:
            current_agent = self.agents.get(self.current_agent_type)
            if current_agent and hasattr(current_agent, 'memory_manager'):
                return current_agent.memory_manager.restore_session(session_id)
            else:
                return False
        except Exception as e:
            logger.error(f"Failed to restore session: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            current_agent = self.agents.get(self.current_agent_type)
            if current_agent and hasattr(current_agent, 'memory_manager'):
                return current_agent.memory_manager.delete_session(session_id)
            else:
                return False
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False

    async def create_new_session(self) -> str:
        """创建新会话"""
        try:
            # 获取当前Agent的内存管理器
            current_agent = self.agents.get(self.current_agent_type)
            if current_agent and hasattr(current_agent, 'memory_manager'):
                # 创建新会话
                new_session_id = await current_agent.memory_manager.create_session()
                self.current_session_id = new_session_id
                logger.info(f"Created new session: {new_session_id}")
                return new_session_id
            else:
                # 如果没有内存管理器，生成一个临时ID
                import uuid
                new_session_id = str(uuid.uuid4())
                self.current_session_id = new_session_id
                logger.info(f"Created temporary session: {new_session_id}")
                return new_session_id
        except Exception as e:
            logger.error(f"Failed to create new session: {e}")
            # 生成一个临时ID作为备用
            import uuid
            new_session_id = str(uuid.uuid4())
            self.current_session_id = new_session_id
            return new_session_id
    
    def get_session_id(self) -> Optional[str]:
        """获取当前会话 ID"""
        return self.current_session_id

    async def clear_session_memory(self, session_id: str = None) -> bool:
        """清除会话记忆，保持会话ID不变"""
        try:
            target_session_id = session_id or self.current_session_id
            if not target_session_id:
                logger.warning("No session ID provided for clearing memory")
                return False

            # 获取当前Agent并清除内存
            current_agent = self.agents.get(self.current_agent_type)
            if current_agent:
                # 尝试不同的清除内存方法
                if hasattr(current_agent, 'clear_memory'):
                    # LangChain核心Agent的方法
                    success = await current_agent.clear_memory(target_session_id)
                elif hasattr(current_agent, 'memory_manager'):
                    # 其他Agent的内存管理器
                    success = await current_agent.memory_manager.clear_messages(target_session_id)
                else:
                    # 如果没有专门的方法，尝试直接清除
                    success = True
                    logger.info("Agent doesn't have specific memory clearing method, assuming success")

                if success:
                    logger.info(f"Cleared memory for session: {target_session_id}")
                    return True
                else:
                    logger.warning(f"Failed to clear memory for session: {target_session_id}")
                    return False
            else:
                logger.warning("No current agent available")
                return False
        except Exception as e:
            logger.error(f"Failed to clear session memory: {e}")
            return False

    def get_tools_info(self) -> Dict[str, Any]:
        """获取工具信息"""
        try:
            from .base.tool_base import tool_registry

            all_tools = tool_registry.get_all_tools()

            builtin_tools = []
            custom_tools = []

            for tool_name, tool in all_tools.items():
                tool_info = {
                    "name": tool.name,
                    "description": tool.description,
                    "type": tool.tool_type.value if hasattr(tool.tool_type, 'value') else str(tool.tool_type),
                    "initialized": tool._initialized if hasattr(tool, '_initialized') else False
                }

                # 获取工具参数
                try:
                    schema = tool.get_schema()
                    tool_info["parameters"] = {
                        param.name: {
                            "type": param.type,
                            "description": param.description,
                            "required": param.required,
                            "default": param.default
                        } for param in schema.parameters
                    }
                except:
                    tool_info["parameters"] = {}

                # 根据工具类型分类
                if hasattr(tool, 'tool_type') and 'custom' in str(tool.tool_type).lower():
                    custom_tools.append(tool_info)
                else:
                    builtin_tools.append(tool_info)

            return {
                "builtin": builtin_tools,
                "custom": custom_tools,
                "total_count": len(all_tools)
            }

        except Exception as e:
            logger.error(f"Failed to get tools info: {e}")
            return {
                "builtin": [],
                "custom": [],
                "total_count": 0,
                "error": str(e)
            }



    def get_sessions(self) -> List[Dict[str, Any]]:
        """获取会话列表"""
        try:
            # 这里应该从记忆管理器获取会话列表
            # 暂时返回空列表，实际实现需要根据记忆管理器的接口
            return []
        except Exception as e:
            logger.error(f"Failed to get sessions: {e}")
            return []

    def create_session(self) -> str:
        """创建新会话"""
        try:
            import uuid
            session_id = str(uuid.uuid4())
            return session_id
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return ""

    def get_supported_models(self) -> Dict[str, Any]:
        """获取支持的模型"""
        try:
            return config.SUPPORTED_MODELS
        except Exception as e:
            logger.error(f"Failed to get supported models: {e}")
            return {}

    def get_current_model(self) -> Dict[str, Any]:
        """获取当前模型配置"""
        try:
            return {
                "provider": config.MODEL_PROVIDER,
                "model": config.get_model_config().get("model", ""),
                "base_url": config.get_model_config().get("base_url", ""),
                "temperature": config.get_model_config().get("temperature", 0.7)
            }
        except Exception as e:
            logger.error(f"Failed to get current model: {e}")
            return {}

    async def switch_agent_model(self, agent_type: str, new_model: str) -> bool:
        """为指定Agent切换底层模型"""
        try:
            # 验证agent_type
            if agent_type not in self.agents:
                logger.error(f"Agent type {agent_type} not found")
                return False

            # 验证模型是否在支持列表中
            supported_models = config.SUPPORTED_MODELS.get("ollama", {}).get("models", [])
            if new_model not in supported_models:
                logger.error(f"Model {new_model} not in supported models: {supported_models}")
                return False

            # 获取目标Agent
            target_agent = self.agents[agent_type]

            # 检查Agent是否有模型切换方法
            if hasattr(target_agent, 'switch_model'):
                success = await target_agent.switch_model(new_model)
                if success:
                    logger.info(f"Successfully switched {agent_type} to model {new_model}")
                    return True
                else:
                    logger.error(f"Failed to switch {agent_type} to model {new_model}")
                    return False
            else:
                # 如果Agent没有switch_model方法，尝试重新初始化
                logger.info(f"Agent {agent_type} doesn't support model switching, trying reinitialization")

                # 临时更新配置
                old_model = config.get_model_config().get("model", "")
                config.MODEL_CONFIG["model"] = new_model

                try:
                    # 重新初始化Agent
                    success = await target_agent.initialize()
                    if success:
                        logger.info(f"Successfully reinitialized {agent_type} with model {new_model}")
                        return True
                    else:
                        # 恢复原模型配置
                        config.MODEL_CONFIG["model"] = old_model
                        logger.error(f"Failed to reinitialize {agent_type} with model {new_model}")
                        return False
                except Exception as e:
                    # 恢复原模型配置
                    config.MODEL_CONFIG["model"] = old_model
                    logger.error(f"Error during reinitialization: {e}")
                    return False

        except Exception as e:
            logger.error(f"Failed to switch agent model: {e}")
            return False

    def get_agent_model_info(self, agent_type: str) -> Dict[str, Any]:
        """获取指定Agent的模型信息"""
        try:
            if agent_type not in self.agents:
                return {}

            agent = self.agents[agent_type]

            # 尝试获取Agent的模型信息
            if hasattr(agent, 'get_model_info'):
                return agent.get_model_info()
            elif hasattr(agent, 'model'):
                return {"current_model": agent.model}
            else:
                return {"current_model": config.get_model_config().get("model", "")}

        except Exception as e:
            logger.error(f"Failed to get agent model info: {e}")
            return {}

    def get_status(self) -> Dict[str, Any]:
        """获取 API 状态"""
        return {
            "initialized": self.initialized,
            "available_agents": self.get_available_agents(),
            "current_agent": self.get_current_agent_type(),
            "session_id": self.current_session_id
        }
    
    async def shutdown(self):
        """关闭 API"""
        try:
            # 关闭所有 Agent
            for agent_type, agent in self.agents.items():
                try:
                    if hasattr(agent, 'shutdown'):
                        await agent.shutdown()
                    logger.info(f"Shutdown {agent_type} agent")
                except Exception as e:
                    logger.error(f"Error shutting down {agent_type} agent: {e}")
            
            self.agents.clear()
            self.current_agent = None
            self.current_session_id = None
            self.initialized = False
            
            logger.info("Agent API shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during API shutdown: {e}")


# 全局 API 实例
agent_api = AgentAPI()
