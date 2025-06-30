#!/usr/bin/env python3
"""
Gradio前端界面 - 完整功能版本
支持完全自定义的聊天界面、多页面导航、工具管理、会话管理、开发者模式等
"""

import gradio as gr
import asyncio
import time
import json
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api import agent_api
from backend.utils.logger import get_logger
from backend.config import Config

logger = get_logger(__name__)

class GradioLangChainApp:
    def __init__(self):
        # 会话状态
        self.session_id = None
        self.chat_history = []
        self.initialized = False

        # 配置状态
        self.current_agent_type = "langchain_core"  # 使用默认的LangChain核心Agent
        self.current_model = "ollama"
        self.current_model_name = "qwen:8b"
        self.stream_enabled = True

        # 页面状态
        self.current_page = "chat"
        self.selected_session = None
        self.show_session_detail = False

        # 工具状态
        self.tools_info = {}
        self.tool_test_results = {}

        # 开发者模式 - 交互追踪
        self.latest_interaction = {
            "timestamp": None,
            "user_message": None,
            "raw_response": None,
            "api_call_details": None,
            "execution_steps": [],
            "tool_calls": [],
            "thinking_process": None,
            "model_info": None,
            "performance_metrics": {},
            # 新增：详细的函数调用追踪
            "function_calls": [],
            "execution_flow": [],
            "langchain_chain": [],
            "backend_calls": [],
            "model_interactions": []
        }
        
    def _log_function_call(self, function_name: str, args: dict = None, result: any = None, duration: float = None):
        """记录函数调用详情 - 用于开发者模式追踪"""
        call_info = {
            "timestamp": datetime.now().isoformat(),
            "function": function_name,
            "args": args or {},
            "result_type": type(result).__name__ if result is not None else "None",
            "duration": duration,
            "success": result is not None
        }

        if hasattr(self, 'latest_interaction') and self.latest_interaction:
            self.latest_interaction["function_calls"].append(call_info)

    def _log_execution_step(self, step_name: str, details: str, step_type: str = "process"):
        """记录执行步骤详情"""
        step_info = {
            "timestamp": datetime.now().isoformat(),
            "step": step_name,
            "details": details,
            "type": step_type  # process, api_call, tool_call, model_call
        }

        if hasattr(self, 'latest_interaction') and self.latest_interaction:
            self.latest_interaction["execution_flow"].append(step_info)

    def _log_backend_call(self, api_method: str, params: dict, response: dict):
        """记录后端API调用详情"""
        call_info = {
            "timestamp": datetime.now().isoformat(),
            "method": api_method,
            "parameters": params,
            "response_summary": {
                "success": response.get("success", False),
                "content_length": len(str(response.get("content", ""))) if response.get("content") else 0,
                "has_tool_calls": bool(response.get("tool_calls")),
                "has_thinking": bool(response.get("thinking_process"))
            }
        }

        if hasattr(self, 'latest_interaction') and self.latest_interaction:
            self.latest_interaction["backend_calls"].append(call_info)

    def initialize_session(self):
        """初始化会话"""
        start_time = time.time()
        try:
            if not self.session_id:
                self.session_id = f"gradio_session_{int(time.time())}"
                self.initialized = True
                logger.info(f"会话初始化成功: {self.session_id}")

                # 记录函数调用
                duration = time.time() - start_time
                self._log_function_call("initialize_session",
                                      {"session_id": self.session_id},
                                      "success", duration)

            return f"✅ 会话已初始化: {self.session_id}"
        except Exception as e:
            logger.error(f"会话初始化失败: {e}")
            duration = time.time() - start_time
            self._log_function_call("initialize_session", {}, str(e), duration)
            return f"❌ 会话初始化失败: {str(e)}"
    
    def update_agent_config(self, agent_type: str, model_provider: str, model_name: str, stream: bool):
        """更新代理配置"""
        try:
            # 切换Agent类型
            if agent_type != self.current_agent_type:
                success = agent_api.set_current_agent(agent_type)
                if not success:
                    return f"❌ 切换Agent失败: {agent_type} 不可用"

            # 更新模型配置
            try:
                Config.set_model_config(model_provider, model_name)
                logger.info(f"模型配置已更新: {model_provider} | {model_name}")

                # 重新初始化Agent以应用新的模型配置
                import asyncio
                reinit_success = asyncio.run(agent_api.reinitialize_current_agent())
                if not reinit_success:
                    logger.warning("Agent重新初始化失败，可能仍使用旧配置")
                else:
                    logger.info("Agent重新初始化成功，新模型配置已生效")

            except Exception as e:
                logger.warning(f"模型配置更新失败: {e}")
                return f"❌ 模型配置更新失败: {str(e)}"

            # 更新前端状态
            self.current_agent_type = agent_type
            self.current_model = model_provider
            self.current_model_name = model_name
            self.stream_enabled = stream

            # 获取Agent信息确认切换成功
            current_agent = agent_api.get_current_agent_type()

            # 检查模型是否支持工具调用
            supports_tools = Config.model_supports_tools(model_provider, model_name)
            tool_status = "支持工具调用" if supports_tools else "不支持工具调用"

            return f"✅ 配置已更新并重新初始化: {current_agent} | {model_provider} | {model_name} | 流式: {stream} | {tool_status}"

        except Exception as e:
            logger.error(f"更新配置失败: {e}")
            return f"❌ 配置更新失败: {str(e)}"
    
    async def process_message(self, message: str, history: List[Dict[str, str]]):
        """处理用户消息 - 渐进式显示"""
        if not message.strip():
            yield history, ""
            return

        # 初始化会话
        if not self.session_id:
            self.initialize_session()

        # 添加用户消息到历史 (使用新的messages格式)
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": ""})
        yield history, ""

        # 开始计时
        start_time = time.time()

        # 开发者模式 - 记录交互开始
        self.latest_interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_message": message,
            "raw_response": None,
            "api_call_details": {
                "agent_type": self.current_agent_type,
                "model_provider": self.current_model,
                "model_name": self.current_model_name,
                "session_id": self.session_id,
                "stream_enabled": self.stream_enabled
            },
            "execution_steps": [],
            "tool_calls": [],
            "thinking_process": None,
            "model_info": f"{self.current_agent_type.upper()} | {self.current_model} | {self.current_model_name}",
            "performance_metrics": {
                "start_time": start_time,
                "end_time": None,
                "total_duration": None,
                "thinking_duration": None,
                "execution_duration": None
            },
            # 详细追踪信息
            "function_calls": [],
            "execution_flow": [],
            "langchain_chain": [],
            "backend_calls": [],
            "model_interactions": []
        }

        # 记录函数调用开始
        self._log_function_call("process_message", {"message_length": len(message), "history_length": len(history)})
        self._log_execution_step("消息处理开始", f"用户消息: {message[:50]}{'...' if len(message) > 50 else ''}", "process")

        # 阶段1: 思考过程 - 实时显示
        thinking_msg = """
<details open>
<summary>🧠 <strong>AI 思考过程</strong></summary>

🤔 正在连接AI模型...
</details>
"""
        history[-1]["content"] = thinking_msg
        yield history, ""

        # 实时更新思考状态
        thinking_steps = [
            "🔍 正在理解您的需求...",
            "🧩 正在分析问题复杂度...",
            "🎯 正在制定解决方案...",
            "✅ 思考完成，准备执行..."
        ]

        for i, step in enumerate(thinking_steps):
            elapsed = time.time() - start_time
            thinking_msg = f"""
<details open>
<summary>🧠 <strong>AI 思考过程</strong></summary>

⏱️ 思考时间: {elapsed:.1f}秒
{step}
</details>
"""
            history[-1]["content"] = thinking_msg
            yield history, ""
            await asyncio.sleep(0.1)  # 减少抖动

        # 阶段2: 执行过程开始
        elapsed = time.time() - start_time
        execution_msg = f"""
<details>
<summary>🧠 <strong>AI 思考过程</strong> ⏱️ {elapsed:.1f}秒</summary>

✅ 思考完成，已分析用户需求并制定解决方案
</details>

<details open>
<summary>⚙️ <strong>AI 执行过程</strong></summary>

🔄 正在建立连接...
</details>
"""
        history[-1]["content"] = execution_msg
        yield history, ""
        
        try:
            if self.stream_enabled:
                # 记录流式响应开始
                self._log_execution_step("流式响应开始", "启动流式处理模式", "api_call")
                self._log_function_call("agent_api.chat_stream", {"message": message, "session_id": self.session_id})

                # 流式响应 - 真实的流式处理
                full_response = ""
                thinking_process = ""
                tool_calls = []

                # 显示连接状态
                elapsed = time.time() - start_time
                execution_msg = (
                    f"🧠 **AI 思考过程**\n\n"
                    f"⏱️ 思考时间: {elapsed:.1f}秒\n"
                    f"✅ 思考完成\n\n"
                    f"⚙️ **AI 执行过程**\n\n"
                    f"📡 已建立流式连接，等待响应..."
                )
                history[-1]["content"] = execution_msg
                yield history, ""

                # 记录后端API调用
                self._log_backend_call("chat_stream",
                                     {"message": message, "session_id": self.session_id, "stream": True},
                                     {"status": "connecting"})

                # 用于处理think标签的变量
                current_think_content = ""
                in_think_tag = False

                async for chunk in agent_api.chat_stream(message, self.session_id):
                    if chunk["success"] and not chunk.get("done", False):
                        # 记录模型交互详情
                        chunk_info = {
                            "timestamp": datetime.now().isoformat(),
                            "chunk_type": "content",
                            "content_length": len(chunk.get("content", "")),
                            "has_thinking": bool(chunk.get("thinking_process")),
                            "success": chunk.get("success", False),
                            "done": chunk.get("done", False)
                        }
                        self.latest_interaction["model_interactions"].append(chunk_info)

                        content = chunk["content"]
                        full_response += content

                        # 检测和提取思维链内容（支持多种推理模型）
                        if self._detect_thinking_start(content):
                            in_think_tag = True
                            current_think_content = str(self._extract_thinking_start(content))
                            self._log_execution_step("思维过程开始", "检测到思维标签开始", "model_call")
                        elif self._detect_thinking_end(content) and in_think_tag:
                            current_think_content += str(self._extract_thinking_end(content))
                            in_think_tag = False
                            thinking_process = current_think_content
                            self._log_execution_step("思维过程结束", f"思维内容长度: {len(thinking_process)}", "model_call")
                        elif in_think_tag:
                            current_think_content += str(content)

                        # 实时更新流式内容
                        elapsed = time.time() - start_time

                        # 如果有思维过程，显示它
                        if chunk.get("thinking_process"):
                            thinking_process = chunk["thinking_process"]
                            self._log_execution_step("思维过程更新", f"接收到思维过程: {len(thinking_process)}字符", "model_call")

                        # 构建显示消息

                        if in_think_tag or current_think_content:
                            # 显示实时思考过程
                            display_think = current_think_content if in_think_tag else thinking_process
                            thinking_section = self._create_collapsible_section(
                                f"🧠 AI 思考过程 (⏱️ {elapsed:.1f}秒)",
                                f"```\n{display_think}\n```",
                                "thinking_section",
                                collapsed=True
                            )
                            execution_section = self._create_collapsible_section(
                                "⚙️ AI 执行过程",
                                f"📝 流式生成中... (已生成 {len(full_response)} 字符)",
                                "execution_section",
                                collapsed=True
                            )
                            execution_msg = f"""{thinking_section}

{execution_section}

### 💬 AI 回复

{self._clean_response(full_response)}▌

---
**模型**: {self.current_agent_type.upper()} | {self.current_model} | {self.current_model_name}
"""
                        else:
                            # 常规显示
                            thinking_section = self._create_collapsible_section(
                                f"🧠 AI 思考过程 (⏱️ {elapsed:.1f}秒)",
                                "✅ 思考完成",
                                "thinking_section",
                                collapsed=True
                            )
                            execution_section = self._create_collapsible_section(
                                "⚙️ AI 执行过程",
                                f"📝 流式生成中... (已生成 {len(full_response)} 字符)",
                                "execution_section",
                                collapsed=True
                            )
                            execution_msg = f"""{thinking_section}

{execution_section}

### 💬 AI 回复

{self._clean_response(full_response)}▌

---
**模型**: {self.current_agent_type.upper()} | {self.current_model} | {self.current_model_name}
"""

                        history[-1]["content"] = execution_msg
                        yield history, ""

                    elif chunk.get("done", False):
                        # 获取完整信息
                        thinking_process = chunk.get("thinking_process", thinking_process)
                        tool_calls = chunk.get("tool_calls", [])
                        break
                    elif not chunk["success"]:
                        error_msg = f"❌ 流式响应失败: {chunk.get('error', '未知错误')}"
                        history[-1]["content"] = error_msg
                        yield history, ""
                        return
                        
            else:
                # 普通响应
                response = await agent_api.chat(message, self.session_id)
                
                if response["success"]:
                    full_response = response["content"]
                    thinking_process = response.get("thinking_process", "")
                    tool_calls = response.get("tool_calls", [])
                else:
                    error_msg = f"❌ 响应失败: {response.get('error', '未知错误')}"
                    history[-1]["content"] = error_msg
                    yield history, ""
                    return

            # 阶段3: 最终回复
            elapsed = time.time() - start_time

            # 构建完整的响应消息
            final_msg = self._build_final_message(
                elapsed, thinking_process, tool_calls, full_response
            )

            history[-1]["content"] = final_msg

            # 开发者模式 - 记录交互完成
            end_time = time.time()
            self.latest_interaction.update({
                "raw_response": {
                    "success": True,
                    "content": full_response,
                    "thinking_process": thinking_process,
                    "tool_calls": tool_calls,
                    "metadata": {
                        "response_type": "stream" if self.stream_enabled else "normal",
                        "has_tools": bool(tool_calls),
                        "response_length": len(full_response) if full_response else 0
                    }
                },
                "execution_steps": [
                    f"1. 用户消息接收: {self.latest_interaction['user_message'][:50]}...",
                    f"2. Agent类型: {self.current_agent_type}",
                    f"3. 模型调用: {self.current_model}/{self.current_model_name}",
                    f"4. 响应模式: {'流式' if self.stream_enabled else '普通'}",
                    f"5. 工具调用: {len(tool_calls)}个" if tool_calls else "5. 无工具调用",
                    f"6. 响应生成完成: {len(full_response)}字符" if full_response else "6. 响应生成失败"
                ],
                "tool_calls": tool_calls,
                "thinking_process": thinking_process,
                "performance_metrics": {
                    **self.latest_interaction["performance_metrics"],
                    "end_time": end_time,
                    "total_duration": end_time - start_time,
                    "thinking_duration": elapsed * 0.3,  # 估算思考时间
                    "execution_duration": elapsed * 0.7   # 估算执行时间
                }
            })

            yield history, ""

        except Exception as e:
            logger.error(f"处理消息时出错: {e}")
            error_msg = f"❌ 处理消息时出错: {str(e)}\n\n请检查：\n1. 网络连接是否正常\n2. 后端服务是否运行\n3. 模型配置是否正确"

            # 开发者模式 - 记录错误
            end_time = time.time()
            self.latest_interaction.update({
                "raw_response": {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                "execution_steps": [
                    f"1. 用户消息接收: {self.latest_interaction['user_message'][:50]}...",
                    f"2. Agent类型: {self.current_agent_type}",
                    f"3. 模型调用: {self.current_model}/{self.current_model_name}",
                    f"4. 错误发生: {type(e).__name__}",
                    f"5. 错误信息: {str(e)[:100]}..."
                ],
                "performance_metrics": {
                    **self.latest_interaction["performance_metrics"],
                    "end_time": end_time,
                    "total_duration": end_time - start_time,
                    "error": True
                }
            })

            history[-1]["content"] = error_msg
            yield history, ""
    
    def _build_final_message(self, elapsed: float, thinking_process: str,
                           tool_calls: List[Dict], response: str) -> str:
        """构建最终的响应消息"""
        # 检测工具调用 - 更准确的检测逻辑
        has_tools = bool(tool_calls) or "TOOL_CALL:" in response or "工具执行结果:" in response

        # 提取思维链内容（支持多种推理模型）
        think_content = ""
        if thinking_process:
            # 支持多种思维链格式
            import re
            patterns = [
                r'<think>(.*?)</think>',
                r'<thinking>(.*?)</thinking>',
                r'<reasoning>(.*?)</reasoning>',
                r'<analysis>(.*?)</analysis>'
            ]
            for pattern in patterns:
                match = re.search(pattern, thinking_process, re.DOTALL)
                if match:
                    think_content = match.group(1).strip()
                    break

        # 不再需要AI角色显示，直接构建内容

        # 构建思考过程内容
        thinking_content = f"⏱️ 思考时间: {elapsed:.2f}秒 | 🔧 工具调用: {'是' if has_tools else '否'} | 📝 执行步骤: {len(tool_calls) if tool_calls else (1 if has_tools else 0)}\n\n"

        if think_content:
            thinking_content += f"**🧠 AI 分析过程:**\n```\n{think_content}\n```"
        elif thinking_process and thinking_process.strip():
            thinking_content += f"**🧠 AI 分析过程:**\n```\n{thinking_process}\n```"
        else:
            # 尝试从响应中提取思维过程
            extracted_thinking = self._extract_thinking_from_response(response)
            thinking_content += f"**🧠 AI 分析过程:**\n"
            if extracted_thinking and len(extracted_thinking) > 50:
                thinking_content += f"```\n{extracted_thinking}\n```\n"
            else:
                thinking_content += f"- 分析用户输入并理解需求\n"
                thinking_content += f"- 选择处理策略：{'工具调用模式' if has_tools else '直接回答模式'}\n"
                thinking_content += f"- 生成回复内容：{len(response)}字符\n"
                thinking_content += f"- 当前模型不支持详细思维链输出"

        # 构建执行过程内容
        execution_content = ""
        if has_tools:
            if tool_calls:
                execution_content += "**🔧 工具调用详情:**\n\n"
                for i, tool_call in enumerate(tool_calls, 1):
                    tool_name = tool_call.get("tool", "未知工具")
                    tool_success = tool_call.get("success", True)

                    execution_content += f"**第 {i} 步:** {'✅' if tool_success else '❌'} 调用工具 `{tool_name}`\n"

                    if tool_call.get("parameters"):
                        execution_content += f"📥 **输入参数:** `{json.dumps(tool_call['parameters'], ensure_ascii=False)}`\n"

                    if tool_call.get("result"):
                        result_str = str(tool_call["result"])[:200] + "..." if len(str(tool_call["result"])) > 200 else str(tool_call["result"])
                        execution_content += f"📤 **执行结果:** `{result_str}`\n\n"
            else:
                execution_content += "**🔧 工具调用详情:**\n\n"
                execution_content += "**第 1 步:** ✅ 检测到工具调用\n"
                execution_content += "**第 2 步:** ✅ 工具执行完成"
        else:
            execution_content += "**第 1 步:** ✅ 问题理解完成\n"
            execution_content += "**第 2 步:** ✅ 基于知识库直接生成回答"

        # 处理AI回复 - 清理工具调用信息，只显示AI的整理结果
        clean_response = self._clean_response(response)

        # 组合最终消息 - 使用HTML折叠标签
        final_msg = f"""
<details>
<summary>🧠 <strong>AI 思考过程</strong> ⏱️ {elapsed:.2f}秒</summary>

{thinking_content}
</details>

<details>
<summary>⚙️ <strong>AI 执行过程</strong></summary>

{execution_content}
</details>

### 💬 AI 回复

{clean_response}

---
**模型信息**: {self.current_agent_type.upper()} | {self.current_model} | {self.current_model_name}
"""

        return final_msg

    def _clean_response(self, response: str) -> str:
        """清理响应，移除工具调用的原始信息，保留AI整理的结果"""
        if not response:
            return "❌ 抱歉，AI响应为空，请重试或检查模型连接。"

        # 如果响应包含工具调用信息，尝试提取AI的分析和总结
        if "TOOL_CALL:" in response and "工具执行结果:" in response:
            # 分割响应，查找工具执行结果后的AI分析
            parts = response.split("工具执行结果:")
            if len(parts) > 1:
                # 获取工具结果后的内容
                after_tool = parts[-1].strip()

                # 查找AI的分析或总结
                lines = after_tool.split('\n')
                ai_analysis = []
                tool_result_lines = []

                in_tool_result = True
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # 检测是否是AI的分析开始
                    if any(keyword in line for keyword in ['根据', '基于', '从结果', '可以看到', '显示', '总结', '分析']):
                        in_tool_result = False

                    if in_tool_result:
                        tool_result_lines.append(line)
                    else:
                        ai_analysis.append(line)

                # 如果有AI分析，返回分析内容；否则返回简化的工具结果
                if ai_analysis:
                    return '\n'.join(ai_analysis)
                elif tool_result_lines:
                    # 简化工具结果显示
                    return f"根据查询结果：\n\n{chr(10).join(tool_result_lines[:5])}{'...' if len(tool_result_lines) > 5 else ''}"

        # 移除原始的工具调用格式
        import re
        # 移除 TOOL_CALL: 格式
        clean_text = re.sub(r'TOOL_CALL:\s*\w+\s*PARAMETERS:\s*\{[^}]*\}', '', response)
        # 移除工具执行结果的原始格式
        clean_text = re.sub(r'工具执行结果:\s*使用\s*\w+\s*工具:', '查询结果:', clean_text)

        return clean_text.strip() or "AI已完成处理，请查看上述执行过程。"

    def _detect_thinking_start(self, content: str) -> bool:
        """检测思维链开始标签（支持多种推理模型）"""
        thinking_patterns = [
            "<think>",           # 千问模型
            "<thinking>",        # DeepSeek模型
            "<reasoning>",       # 其他推理模型
            "<analysis>",        # 分析模式
            "思考：",            # 中文模式
            "推理：",            # 中文推理
        ]
        return any(pattern in content for pattern in thinking_patterns)

    def _detect_thinking_end(self, content: str) -> bool:
        """检测思维链结束标签"""
        thinking_end_patterns = [
            "</think>",
            "</thinking>",
            "</reasoning>",
            "</analysis>",
        ]
        return any(pattern in content for pattern in thinking_end_patterns)

    def _extract_thinking_start(self, content: str) -> str:
        """提取思维链开始内容"""
        for pattern in ["<think>", "<thinking>", "<reasoning>", "<analysis>"]:
            if pattern in content:
                return content.split(pattern)[-1]
        return content

    def _extract_thinking_end(self, content: str) -> str:
        """提取思维链结束内容"""
        for pattern in ["</think>", "</thinking>", "</reasoning>", "</analysis>"]:
            if pattern in content:
                return content.split(pattern)[0]
        return content

    def _extract_thinking_from_response(self, response: str) -> str:
        """从响应中提取思维过程"""
        # 支持多种思维链格式
        import re
        patterns = [
            r'<think>(.*?)</think>',
            r'<thinking>(.*?)</thinking>',
            r'<reasoning>(.*?)</reasoning>',
            r'<analysis>(.*?)</analysis>',
            r'思考：(.*?)(?=\n\n|$)',
            r'分析：(.*?)(?=\n\n|$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # 如果没有找到思维链标签，生成基本的思维过程
        return f"处理用户请求：{response[:100]}{'...' if len(response) > 100 else ''}"

    def _create_collapsible_section(self, title: str, content: str, section_id: str = "", collapsed: bool = True) -> str:
        """创建可折叠的内容区域 - 简化为Markdown格式"""
        # 由于Gradio的限制，我们使用简化的展示方式
        status = "🔽" if not collapsed else "▶️"
        return f"""
### {status} {title}

{content}

---
"""

    def _format_user_role(self) -> str:
        """格式化用户角色显示"""
        return "**👤 用户**"

    def _format_ai_role(self) -> str:
        """格式化AI角色显示"""
        model_info = f"{self.current_agent_type.upper()} | {self.current_model} | {self.current_model_name}"
        return f"**🤖 AI ({model_info})**"

    def clear_chat(self):
        """清空聊天历史"""
        self.chat_history = []
        return []

    def break_context(self):
        """切断上下文联系，清除当前会话记忆但保持会话ID"""
        try:
            # 清除当前会话的记忆
            success = asyncio.run(agent_api.clear_session_memory(self.session_id))

            if success:
                # 在聊天历史中添加分隔符
                separator_msg = f"""
---

### ✂️ 上下文已切断 - 记忆已清除

*会话ID: {self.session_id[:8]}... (保持不变)*

---
"""

                logger.info(f"上下文已切断，会话ID保持: {self.session_id}")
                return separator_msg
            else:
                return "❌ 切断上下文失败: 无法清除会话记忆"
        except Exception as e:
            logger.error(f"切断上下文失败: {e}")
            return f"❌ 切断上下文失败: {str(e)}"

    # ==================== 工具管理功能 ====================

    def get_tools_info(self):
        """获取工具信息"""
        try:
            tools_detail = agent_api.get_tools_detail()
            self.tools_info = tools_detail
            return tools_detail
        except Exception as e:
            logger.error(f"获取工具信息失败: {e}")
            return {"builtin_tools": [], "custom_tools": [], "mcp_tools": []}

    def test_tool(self, tool_name: str, parameters: Dict[str, Any]):
        """测试工具调用"""
        try:
            result = asyncio.run(agent_api.test_tool(tool_name, parameters))
            self.tool_test_results[tool_name] = result
            return result
        except Exception as e:
            error_result = {"success": False, "error": str(e)}
            self.tool_test_results[tool_name] = error_result
            return error_result

    def get_tool_config(self, tool_name: str):
        """获取工具配置详情"""
        try:
            # 从工具名称中提取实际工具名
            actual_tool_name = tool_name.split(' ', 1)[1] if ' ' in tool_name else tool_name

            # 获取工具详细信息
            tools_info = agent_api.get_tools_info()

            # 查找工具 - 修复API返回格式
            tool_detail = None
            # 检查新的API格式
            for category in ['builtin', 'custom', 'mcp']:
                for tool in tools_info.get(category, []):
                    if tool['name'] == actual_tool_name:
                        tool_detail = tool
                        break
                if tool_detail:
                    break

            # 如果没找到，尝试旧格式
            if not tool_detail:
                for category in ['builtin_tools', 'custom_tools', 'mcp_tools']:
                    for tool in tools_info.get(category, []):
                        if tool['name'] == actual_tool_name:
                            tool_detail = tool
                            break
                    if tool_detail:
                        break

            if not tool_detail:
                return {"error": f"工具 {actual_tool_name} 不存在"}

            # 构建配置信息
            config_info = {
                "name": tool_detail['name'],
                "description": tool_detail['description'],
                "version": tool_detail.get('version', 'N/A'),
                "parameters": tool_detail.get('parameters', []),
                "required_params": [],
                "optional_params": [],
                "example_config": {}
            }

            # 分析参数 - 支持多种参数格式
            parameters = tool_detail.get('parameters', {})

            # 如果parameters是字典格式（新API格式）
            if isinstance(parameters, dict):
                for param_name, param_data in parameters.items():
                    param_info = {
                        "name": param_name,
                        "type": param_data.get('type', 'string'),
                        "description": param_data.get('description', ''),
                        "default": param_data.get('default', None)
                    }

                    if param_data.get('required', False):
                        config_info['required_params'].append(param_info)
                        config_info['example_config'][param_info['name']] = f"<{param_info['type']}>"
                    else:
                        config_info['optional_params'].append(param_info)
                        if param_info['default'] is not None:
                            config_info['example_config'][param_info['name']] = param_info['default']

            # 如果parameters是列表格式（旧API格式）
            elif isinstance(parameters, list):
                for param in parameters:
                    param_info = {
                        "name": param.get('name', ''),
                        "type": param.get('type', 'string'),
                        "description": param.get('description', ''),
                        "default": param.get('default', None)
                    }

                    if param.get('required', False):
                        config_info['required_params'].append(param_info)
                        config_info['example_config'][param_info['name']] = f"<{param_info['type']}>"
                    else:
                        config_info['optional_params'].append(param_info)
                        if param_info['default'] is not None:
                            config_info['example_config'][param_info['name']] = param_info['default']

            return config_info

        except Exception as e:
            return {"error": str(e)}

    # ==================== 会话管理功能 ====================

    def get_sessions_list(self):
        """获取会话列表"""
        try:
            sessions = agent_api.get_sessions()
            return sessions
        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            return []

    def get_session_detail(self, session_id: str):
        """获取会话详情"""
        try:
            detail = agent_api.get_session_detail(session_id)
            return detail
        except Exception as e:
            logger.error(f"获取会话详情失败: {e}")
            return None

    def delete_session(self, session_id: str):
        """删除会话"""
        try:
            result = agent_api.delete_session(session_id)
            return result
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False

    # ==================== 开发者模式功能 ====================

    def get_latest_interaction_info(self):
        """获取最新的交互信息 - 供开发者模式使用"""
        try:
            if not self.latest_interaction["timestamp"]:
                return {
                    "has_data": False,
                    "message": "暂无交互数据，请先在聊天页面发送消息"
                }

            # 获取LangChain开发者信息
            dev_info = self.latest_interaction.get("dev_info", {})

            return {
                "has_data": True,
                "api_call_info": {
                    "timestamp": self.latest_interaction["timestamp"],
                    "user_message": self.latest_interaction["user_message"],
                    "api_call_details": self.latest_interaction["api_call_details"],
                    "model_info": self.latest_interaction["model_info"]
                },
                "performance_metrics": self.latest_interaction["performance_metrics"],
                "raw_response": self.latest_interaction["raw_response"],
                "execution_steps": self.latest_interaction["execution_steps"],
                "thinking_process": self.latest_interaction["thinking_process"] or "无思维过程记录",
                "tool_calls": self.latest_interaction["tool_calls"],
                # LangChain 特定信息
                "langchain_messages": dev_info.get("messages", []),
                "langchain_function_calls": dev_info.get("function_calls", []),
                "tool_interactions": dev_info.get("tool_interactions", []),
                "processing_steps": dev_info.get("processing_steps", [])
            }
        except Exception as e:
            return {
                "has_data": False,
                "message": f"获取交互信息失败: {str(e)}"
            }

    async def get_agent_info(self):
        """获取Agent信息"""
        try:
            agent_info = await agent_api.get_agent_info()
            current_agent = agent_api.get_current_agent_type()
            return {
                "current_agent": current_agent,
                "agent_info": agent_info,
                "initialized": self.initialized
            }
        except Exception as e:
            logger.error(f"获取Agent信息失败: {e}")
            return {"error": str(e)}

    # ==================== 配置获取方法 ====================

    def get_supported_providers(self):
        """获取支持的模型供应商"""
        try:
            return Config.get_supported_providers()
        except Exception as e:
            logger.error(f"获取模型供应商失败: {e}")
            return ["ollama"]  # 默认返回ollama

    def get_provider_models(self, provider: str):
        """获取指定供应商的模型列表"""
        try:
            return Config.get_provider_models(provider)
        except Exception as e:
            logger.error(f"获取模型列表失败: {e}")
            return ["qwen2.5:7b"]  # 默认返回一个模型

    def get_current_model_config(self):
        """获取当前模型配置"""
        try:
            return Config.get_model_config()
        except Exception as e:
            logger.error(f"获取模型配置失败: {e}")
            return {"provider": "ollama", "model": "qwen2.5:7b"}

    # ==================== 辅助方法 ====================

    def _generate_tools_overview_html(self, tools_detail: Dict) -> str:
        """生成工具概览HTML"""
        html = "<div style='font-family: Arial, sans-serif;'>"

        # 内置工具（LangChain官方）
        if tools_detail.get('builtin_tools'):
            html += "<h3>🏠 内置工具</h3>"
            for tool in tools_detail['builtin_tools']:
                html += f"""
                <div style='border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin: 10px 0; background: #f9f9f9;'>
                    <h4 style='margin: 0 0 10px 0; color: #1976d2;'>🔧 {tool['name']}</h4>
                    <p style='margin: 5px 0; color: #666;'><strong>描述:</strong> {tool['description']}</p>
                    <p style='margin: 5px 0; color: #666;'><strong>版本:</strong> {tool.get('version', 'N/A')}</p>
                    <p style='margin: 5px 0; color: #666;'><strong>参数数量:</strong> {len(tool.get('parameters', []))}</p>
                </div>
                """

        # 自定义工具（用户编写）
        if tools_detail.get('custom_tools'):
            html += "<h3>🔧 自定义工具</h3>"
            for tool in tools_detail['custom_tools']:
                html += f"""
                <div style='border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin: 10px 0; background: #f3e5f5;'>
                    <h4 style='margin: 0 0 10px 0; color: #7b1fa2;'>🔧 {tool['name']}</h4>
                    <p style='margin: 5px 0; color: #666;'><strong>描述:</strong> {tool['description']}</p>
                    <p style='margin: 5px 0; color: #666;'><strong>类型:</strong> {tool.get('type', 'custom')}</p>
                    <p style='margin: 5px 0; color: #666;'><strong>参数数量:</strong> {len(tool.get('parameters', []))}</p>
                </div>
                """

        # MCP工具
        if tools_detail.get('mcp_tools'):
            html += "<h3>🔗 MCP工具</h3>"
            for tool in tools_detail['mcp_tools']:
                html += f"""
                <div style='border: 1px solid #e0e0e0; border-radius: 8px; padding: 15px; margin: 10px 0; background: #e8f5e8;'>
                    <h4 style='margin: 0 0 10px 0; color: #388e3c;'>🔧 {tool['name']}</h4>
                    <p style='margin: 5px 0; color: #666;'><strong>描述:</strong> {tool['description']}</p>
                    <p style='margin: 5px 0; color: #666;'><strong>版本:</strong> {tool.get('version', 'N/A')}</p>
                    <p style='margin: 5px 0; color: #666;'><strong>参数数量:</strong> {len(tool.get('parameters', []))}</p>
                </div>
                """

        if not any([tools_detail.get('builtin_tools'), tools_detail.get('custom_tools'), tools_detail.get('mcp_tools')]):
            html += "<p style='color: #666; text-align: center; padding: 20px;'>暂无可用工具</p>"

        html += "</div>"
        return html

    def _format_agent_info_html(self, agent_info: Dict) -> str:
        """格式化Agent信息HTML"""
        current_agent = agent_info.get("current_agent", "unknown")

        html = f"""
        <div style='font-family: Arial, sans-serif;'>
            <div style='background: #e3f2fd; border: 1px solid #2196f3; border-radius: 8px; padding: 15px; margin: 10px 0;'>
                <h4 style='margin: 0 0 10px 0; color: #1976d2;'>🤖 当前Agent: {current_agent.upper()}</h4>
                <p><strong>初始化状态:</strong> {'✅ 已初始化' if agent_info.get('initialized') else '❌ 未初始化'}</p>
                <p><strong>Agent类型特点:</strong></p>
                <ul>
        """

        if current_agent == "chain":
            html += """
                    <li><strong>Chain模式:</strong> 简单的链式调用，适合线性处理流程</li>
                    <li><strong>工具调用:</strong> 通过LangChain的工具绑定机制</li>
                    <li><strong>执行方式:</strong> 顺序执行，每个步骤依次处理</li>
                    <li><strong>适用场景:</strong> 简单的问答、基础工具调用</li>
            """
        elif current_agent == "agent":
            html += """
                    <li><strong>Agent模式:</strong> 智能代理，能够自主决策和规划</li>
                    <li><strong>工具调用:</strong> 动态选择和组合工具</li>
                    <li><strong>执行方式:</strong> 基于ReAct模式的思考-行动循环</li>
                    <li><strong>适用场景:</strong> 复杂任务规划、多步骤推理</li>
            """
        elif current_agent == "langgraph":
            html += """
                    <li><strong>LangGraph模式:</strong> 状态图驱动的复杂工作流</li>
                    <li><strong>工具调用:</strong> 基于状态转换的工具调用</li>
                    <li><strong>执行方式:</strong> 状态机模式，支持复杂的分支和循环</li>
                    <li><strong>适用场景:</strong> 复杂业务流程、多轮对话管理</li>
            """

        html += """
                </ul>
            </div>
        </div>
        """
        return html

    def _generate_agent_comparison_html(self) -> str:
        """生成Agent对比HTML"""
        return """
        <div style='font-family: Arial, sans-serif;'>
            <table style='width: 100%; border-collapse: collapse; margin: 10px 0;'>
                <thead>
                    <tr style='background: #f5f5f5;'>
                        <th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>特性</th>
                        <th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>Chain</th>
                        <th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>Agent</th>
                        <th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>LangGraph</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style='border: 1px solid #ddd; padding: 8px;'><strong>复杂度</strong></td>
                        <td style='border: 1px solid #ddd; padding: 8px;'>🟢 简单</td>
                        <td style='border: 1px solid #ddd; padding: 8px;'>🟡 中等</td>
                        <td style='border: 1px solid #ddd; padding: 8px;'>🔴 复杂</td>
                    </tr>
                    <tr>
                        <td style='border: 1px solid #ddd; padding: 8px;'><strong>工具调用</strong></td>
                        <td style='border: 1px solid #ddd; padding: 8px;'>基础绑定</td>
                        <td style='border: 1px solid #ddd; padding: 8px;'>智能选择</td>
                        <td style='border: 1px solid #ddd; padding: 8px;'>状态驱动</td>
                    </tr>
                    <tr>
                        <td style='border: 1px solid #ddd; padding: 8px;'><strong>执行模式</strong></td>
                        <td style='border: 1px solid #ddd; padding: 8px;'>线性链式</td>
                        <td style='border: 1px solid #ddd; padding: 8px;'>ReAct循环</td>
                        <td style='border: 1px solid #ddd; padding: 8px;'>状态图</td>
                    </tr>
                    <tr>
                        <td style='border: 1px solid #ddd; padding: 8px;'><strong>适用场景</strong></td>
                        <td style='border: 1px solid #ddd; padding: 8px;'>简单问答</td>
                        <td style='border: 1px solid #ddd; padding: 8px;'>复杂推理</td>
                        <td style='border: 1px solid #ddd; padding: 8px;'>工作流程</td>
                    </tr>
                    <tr>
                        <td style='border: 1px solid #ddd; padding: 8px;'><strong>学习难度</strong></td>
                        <td style='border: 1px solid #ddd; padding: 8px;'>⭐</td>
                        <td style='border: 1px solid #ddd; padding: 8px;'>⭐⭐⭐</td>
                        <td style='border: 1px solid #ddd; padding: 8px;'>⭐⭐⭐⭐⭐</td>
                    </tr>
                </tbody>
            </table>
        </div>
        """

    def _format_system_info_html(self) -> str:
        """格式化系统信息HTML"""
        try:
            import psutil
            import platform

            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            html = f"""
            <div style='font-family: Arial, sans-serif;'>
                <div style='background: #f3e5f5; border: 1px solid #9c27b0; border-radius: 8px; padding: 15px; margin: 10px 0;'>
                    <h4 style='margin: 0 0 10px 0; color: #7b1fa2;'>💻 系统状态</h4>
                    <p><strong>操作系统:</strong> {platform.system()} {platform.release()}</p>
                    <p><strong>Python版本:</strong> {platform.python_version()}</p>
                    <p><strong>CPU使用率:</strong> {cpu_percent}%</p>
                    <p><strong>内存使用:</strong> {memory.percent}% ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)</p>
                    <p><strong>磁盘使用:</strong> {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)</p>
                    <p><strong>当前时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
            """
        except Exception as e:
            html = f"<div style='color: red;'>❌ 获取系统信息失败: {str(e)}</div>"

        return html

    def _format_memory_info_html(self) -> str:
        """格式化内存信息HTML"""
        html = f"""
        <div style='font-family: Arial, sans-serif;'>
            <div style='background: #e8f5e8; border: 1px solid #4caf50; border-radius: 8px; padding: 15px; margin: 10px 0;'>
                <h4 style='margin: 0 0 10px 0; color: #388e3c;'>🧠 会话内存</h4>
                <p><strong>当前会话ID:</strong> {self.session_id or '未初始化'}</p>
                <p><strong>聊天历史长度:</strong> {len(self.chat_history)}</p>
                <p><strong>初始化状态:</strong> {'✅ 已初始化' if self.initialized else '❌ 未初始化'}</p>
                <p><strong>流式输出:</strong> {'✅ 启用' if self.stream_enabled else '❌ 禁用'}</p>
                <p><strong>当前Agent:</strong> {self.current_agent_type}</p>
                <p><strong>当前模型:</strong> {self.current_model} | {self.current_model_name}</p>
            </div>
        </div>
        """
        return html

    def _execute_test_with_details(self, test_message: str) -> Dict:
        """执行测试并获取详细信息"""
        try:
            import time
            start_time = time.time()

            # 执行测试
            result = asyncio.run(agent_api.chat(test_message, self.session_id))

            execution_time = time.time() - start_time

            return {
                "success": result.get("success", False),
                "content": result.get("content", ""),
                "thinking_process": result.get("thinking_process", ""),
                "tool_calls": result.get("tool_calls", []),
                "execution_steps": result.get("execution_steps", []),
                "execution_time": execution_time,
                "metadata": result.get("metadata", {}),
                "raw_response": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_time": 0
            }

    def _format_response_details_html(self, result: Dict) -> str:
        """格式化响应详情HTML"""
        if not result.get("success"):
            return f"<div style='color: red;'>❌ 执行失败: {result.get('error', '未知错误')}</div>"

        html = f"""
        <div style='font-family: Arial, sans-serif;'>
            <div style='background: #e3f2fd; border: 1px solid #2196f3; border-radius: 8px; padding: 15px; margin: 10px 0;'>
                <h4 style='margin: 0 0 10px 0; color: #1976d2;'>📊 响应分析</h4>
                <p><strong>执行时间:</strong> {result.get('execution_time', 0):.2f}秒</p>
                <p><strong>工具调用次数:</strong> {len(result.get('tool_calls', []))}</p>
                <p><strong>执行步骤数:</strong> {len(result.get('execution_steps', []))}</p>
            </div>

            <div style='background: #f3e5f5; border: 1px solid #9c27b0; border-radius: 8px; padding: 15px; margin: 10px 0;'>
                <h4 style='margin: 0 0 10px 0; color: #7b1fa2;'>🧠 思考过程</h4>
                <pre style='background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap;'>{result.get('thinking_process', '无思考过程记录')}</pre>
            </div>

            <div style='background: #e8f5e8; border: 1px solid #4caf50; border-radius: 8px; padding: 15px; margin: 10px 0;'>
                <h4 style='margin: 0 0 10px 0; color: #388e3c;'>🔧 工具调用详情</h4>
        """

        tool_calls = result.get('tool_calls', [])
        if tool_calls:
            for i, tool_call in enumerate(tool_calls, 1):
                html += f"""
                <div style='margin: 10px 0; padding: 10px; background: #f9f9f9; border-radius: 4px;'>
                    <p><strong>第{i}次调用:</strong> {tool_call.get('tool', 'unknown')}</p>
                    <p><strong>参数:</strong> <code>{json.dumps(tool_call.get('parameters', {}), ensure_ascii=False)}</code></p>
                    <p><strong>结果:</strong> <code>{str(tool_call.get('result', ''))[:200]}...</code></p>
                    <p><strong>状态:</strong> {'✅ 成功' if tool_call.get('success') else '❌ 失败'}</p>
                </div>
                """
        else:
            html += "<p>无工具调用</p>"

        html += """
            </div>

            <div style='background: #fff3e0; border: 1px solid #ff9800; border-radius: 8px; padding: 15px; margin: 10px 0;'>
                <h4 style='margin: 0 0 10px 0; color: #f57c00;'>📋 原始响应对象</h4>
                <pre style='background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; max-height: 300px; white-space: pre-wrap;'>{json.dumps(result.get('raw_response', {}), indent=2, ensure_ascii=False)}</pre>
            </div>
        </div>
        """

        return html

    def _format_test_result_html(self, result: Dict, tool_name: str) -> str:
        """格式化测试结果HTML"""
        if result.get('success'):
            html = f"""
            <div style='font-family: Arial, sans-serif;'>
                <div style='background: #e8f5e8; border: 1px solid #4caf50; border-radius: 8px; padding: 15px; margin: 10px 0;'>
                    <h4 style='margin: 0 0 10px 0; color: #388e3c;'>✅ 工具 {tool_name} 执行成功</h4>
                    <p style='margin: 5px 0;'><strong>执行时间:</strong> {result.get('execution_time', 'N/A')}秒</p>
                    <div style='margin: 10px 0;'>
                        <strong>执行结果:</strong>
                        <pre style='background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto;'>{json.dumps(result.get('result', ''), indent=2, ensure_ascii=False)}</pre>
                    </div>
                </div>
            </div>
            """
        else:
            html = f"""
            <div style='font-family: Arial, sans-serif;'>
                <div style='background: #ffebee; border: 1px solid #f44336; border-radius: 8px; padding: 15px; margin: 10px 0;'>
                    <h4 style='margin: 0 0 10px 0; color: #d32f2f;'>❌ 工具 {tool_name} 执行失败</h4>
                    <div style='margin: 10px 0;'>
                        <strong>错误信息:</strong>
                        <pre style='background: #f5f5f5; padding: 10px; border-radius: 4px; color: #d32f2f;'>{result.get('error', '未知错误')}</pre>
                    </div>
                </div>
            </div>
            """
        return html

    # ==================== 页面创建方法 ====================

    def create_tools_page(self):
        """创建工具管理页面"""
        gr.Markdown("## 🔧 工具管理中心")
        gr.Markdown("*查看、配置和测试所有可用工具*")

        # 工具统计信息
        with gr.Row():
            total_tools_display = gr.Number(label="📊 总工具数", value=0, interactive=False)
            builtin_tools_display = gr.Number(label="🏠 内置工具", value=0, interactive=False)
            custom_tools_display = gr.Number(label="🔧 自定义工具", value=0, interactive=False)
            mcp_tools_display = gr.Number(label="🔗 MCP工具", value=0, interactive=False)

        with gr.Row():
            refresh_tools_btn = gr.Button("🔄 刷新工具列表", variant="secondary")

        # 工具管理标签页
        with gr.Tabs():
            # 工具概览标签页
            with gr.TabItem("📊 工具概览"):
                tools_overview_display = gr.HTML(value="<p>点击刷新按钮加载工具信息</p>")

            # 工具测试标签页
            with gr.TabItem("🧪 工具测试"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 🧪 工具测试")
                        tool_name_dropdown = gr.Dropdown(
                            label="选择工具",
                            choices=[],
                            interactive=True
                        )
                        tool_params_input = gr.Textbox(
                            label="参数 (JSON格式)",
                            placeholder='{"param1": "value1", "param2": "value2"}',
                            lines=5
                        )
                        test_tool_btn = gr.Button("🚀 执行测试", variant="primary")

                    with gr.Column():
                        gr.Markdown("### 📤 测试结果")
                        tool_test_result = gr.HTML(value="<p>等待测试结果...</p>")

            # 工具配置标签页
            with gr.TabItem("⚙️ 工具配置"):
                gr.Markdown("### 🔧 简单工具配置")
                gr.Markdown("*直接填写参数，无需编辑JSON*")

                # 常用工具快速配置
                with gr.Accordion("🚀 常用工具快速配置", open=True):
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("**计算器工具**")
                            calc_precision = gr.Slider(
                                minimum=1, maximum=20, value=10, step=1,
                                label="计算精度", info="小数位数"
                            )
                            calc_format = gr.Dropdown(
                                choices=["auto", "decimal", "scientific", "fraction"],
                                value="auto",
                                label="结果格式"
                            )

                        with gr.Column():
                            gr.Markdown("**文件工具**")
                            file_default_path = gr.Dropdown(
                                choices=["desktop", "documents", "downloads", "home"],
                                value="desktop",
                                label="默认路径"
                            )
                            file_show_hidden = gr.Checkbox(
                                label="显示隐藏文件",
                                value=False
                            )

                        with gr.Column():
                            gr.Markdown("**搜索工具**")
                            search_type = gr.Dropdown(
                                choices=["web", "local"],
                                value="web",
                                label="搜索类型"
                            )
                            search_max_results = gr.Slider(
                                minimum=1, maximum=20, value=5, step=1,
                                label="最大结果数"
                            )

                with gr.Row():
                    save_quick_config_btn = gr.Button("💾 保存快速配置", variant="primary")
                    reset_quick_config_btn = gr.Button("🔄 重置为默认", variant="secondary")

                # 高级配置（JSON方式）
                with gr.Accordion("🔧 高级配置 (JSON)", open=False):
                    with gr.Row():
                        with gr.Column():
                            config_tool_dropdown = gr.Dropdown(
                                label="选择要配置的工具",
                                choices=[],
                                interactive=True
                            )
                            config_params_input = gr.Textbox(
                                label="配置参数 (JSON格式)",
                                placeholder='{"param1": "value1", "param2": "value2"}',
                                lines=5
                            )
                            save_config_btn = gr.Button("💾 保存配置", variant="primary")

                        with gr.Column():
                            gr.Markdown("### 📋 当前配置")
                            current_config_display = gr.HTML(value="<p>选择工具查看当前配置</p>")

                config_status = gr.Markdown("")

        # 快速配置保存功能
        def save_quick_config(calc_prec, calc_fmt, file_path, file_hidden, search_type_val, search_max):
            """保存快速配置"""
            try:
                # 构建配置
                config_updates = {
                    "calculator": {
                        "precision": int(calc_prec),
                        "format_type": calc_fmt
                    },
                    "file_tool": {
                        "action": "list",
                        "path": file_path,
                        "show_hidden": file_hidden
                    },
                    "search": {
                        "search_type": search_type_val,
                        "max_results": int(search_max)
                    }
                }

                # 保存每个工具的配置
                success_count = 0
                for tool_name, config in config_updates.items():
                    try:
                        if agent_api.update_tool_config(tool_name, config):
                            success_count += 1
                    except Exception as e:
                        logger.error(f"Failed to save config for {tool_name}: {e}")

                if success_count == len(config_updates):
                    return "✅ 所有工具配置保存成功！"
                else:
                    return f"⚠️ 部分配置保存成功 ({success_count}/{len(config_updates)})"

            except Exception as e:
                logger.error(f"Failed to save quick config: {e}")
                return f"❌ 保存失败: {str(e)}"

        def reset_quick_config():
            """重置为默认配置"""
            return (
                10,  # calc_precision
                "auto",  # calc_format
                "desktop",  # file_default_path
                False,  # file_show_hidden
                "web",  # search_type
                5,  # search_max_results
                "🔄 已重置为默认配置"
            )

        # 事件绑定
        def refresh_tools_info():
            try:
                tools_detail = self.get_tools_info()

                # 更新统计信息
                total_count = tools_detail.get('total_count', 0)
                builtin_count = len(tools_detail.get('builtin_tools', []))
                custom_count = len(tools_detail.get('custom_tools', []))
                mcp_count = len(tools_detail.get('mcp_tools', []))

                # 生成工具概览HTML
                overview_html = self._generate_tools_overview_html(tools_detail)

                # 生成工具选择列表
                all_tools = []
                for tool in tools_detail.get('builtin_tools', []):
                    all_tools.append(f"🏠 {tool['name']}")
                for tool in tools_detail.get('custom_tools', []):
                    all_tools.append(f"🔧 {tool['name']}")
                for tool in tools_detail.get('mcp_tools', []):
                    all_tools.append(f"🔗 {tool['name']}")

                return (
                    total_count, builtin_count, custom_count, mcp_count,
                    overview_html,
                    gr.update(choices=all_tools),
                    gr.update(choices=all_tools)
                )
            except Exception as e:
                error_html = f"<div style='color: red;'>❌ 获取工具信息失败: {str(e)}</div>"
                return 0, 0, 0, 0, error_html, gr.update(choices=[]), gr.update(choices=[])

        refresh_tools_btn.click(
            fn=refresh_tools_info,
            outputs=[
                total_tools_display, builtin_tools_display, custom_tools_display, mcp_tools_display,
                tools_overview_display, tool_name_dropdown, config_tool_dropdown
            ]
        )

        # 工具测试事件
        def test_tool_wrapper(tool_name_with_prefix, params_str):
            try:
                if not tool_name_with_prefix:
                    return "<div style='color: orange;'>⚠️ 请选择要测试的工具</div>"

                # 提取工具名称（去掉前缀）
                tool_name = tool_name_with_prefix.split(' ', 1)[1] if ' ' in tool_name_with_prefix else tool_name_with_prefix

                params = json.loads(params_str) if params_str.strip() else {}
                result = self.test_tool(tool_name, params)

                return self._format_test_result_html(result, tool_name)
            except json.JSONDecodeError:
                return "<div style='color: red;'>❌ 参数格式错误，请使用有效的JSON格式</div>"
            except Exception as e:
                return f"<div style='color: red;'>❌ 测试失败: {str(e)}</div>"

        test_tool_btn.click(
            fn=test_tool_wrapper,
            inputs=[tool_name_dropdown, tool_params_input],
            outputs=[tool_test_result]
        )

        # 快速配置事件绑定
        save_quick_config_btn.click(
            fn=save_quick_config,
            inputs=[
                calc_precision, calc_format, file_default_path, file_show_hidden,
                search_type, search_max_results
            ],
            outputs=[config_status]
        )

        reset_quick_config_btn.click(
            fn=reset_quick_config,
            outputs=[
                calc_precision, calc_format, file_default_path, file_show_hidden,
                search_type, search_max_results, config_status
            ]
        )

        # 工具配置事件
        def show_tool_config(tool_name_with_prefix):
            try:
                if not tool_name_with_prefix:
                    return "<div style='color: orange;'>⚠️ 请选择要配置的工具</div>", ""

                config_info = self.get_tool_config(tool_name_with_prefix)

                if "error" in config_info:
                    return f"<div style='color: red;'>❌ {config_info['error']}</div>", ""

                # 生成配置显示HTML
                html = f"""
                <div style='font-family: Arial, sans-serif;'>
                    <div style='background: #e3f2fd; border: 1px solid #2196f3; border-radius: 8px; padding: 15px; margin: 10px 0;'>
                        <h4 style='margin: 0 0 10px 0; color: #1976d2;'>🔧 {config_info['name']}</h4>
                        <p><strong>描述:</strong> {config_info['description']}</p>
                        <p><strong>版本:</strong> {config_info['version']}</p>
                    </div>

                    <div style='background: #f3e5f5; border: 1px solid #9c27b0; border-radius: 8px; padding: 15px; margin: 10px 0;'>
                        <h4 style='margin: 0 0 10px 0; color: #7b1fa2;'>📋 必选参数</h4>
                """

                if config_info['required_params']:
                    for param in config_info['required_params']:
                        html += f"""
                        <div style='margin: 8px 0; padding: 8px; background: #fff; border-radius: 4px; border-left: 4px solid #f44336;'>
                            <strong>{param['name']}</strong> ({param['type']}) <span style='color: red;'>*必选</span><br>
                            <small>{param['description']}</small>
                        </div>
                        """
                else:
                    html += "<p>无必选参数</p>"

                html += """
                    </div>

                    <div style='background: #e8f5e8; border: 1px solid #4caf50; border-radius: 8px; padding: 15px; margin: 10px 0;'>
                        <h4 style='margin: 0 0 10px 0; color: #388e3c;'>📋 可选参数</h4>
                """

                if config_info['optional_params']:
                    for param in config_info['optional_params']:
                        default_text = f" (默认: {param['default']})" if param['default'] is not None else ""
                        html += f"""
                        <div style='margin: 8px 0; padding: 8px; background: #fff; border-radius: 4px; border-left: 4px solid #4caf50;'>
                            <strong>{param['name']}</strong> ({param['type']}){default_text}<br>
                            <small>{param['description']}</small>
                        </div>
                        """
                else:
                    html += "<p>无可选参数</p>"

                html += """
                    </div>

                    <div style='background: #fff3e0; border: 1px solid #ff9800; border-radius: 8px; padding: 15px; margin: 10px 0;'>
                        <h4 style='margin: 0 0 10px 0; color: #f57c00;'>💡 后端配置说明</h4>
                        <p>工具配置通常在以下位置进行：</p>
                        <ul>
                            <li><strong>内置工具:</strong> backend/tools/builtin/ 目录下的对应工具文件</li>
                            <li><strong>自定义工具:</strong> backend/tools/custom/ 目录下的对应工具文件</li>
                            <li><strong>环境变量:</strong> .env 文件中配置API密钥等敏感信息</li>
                            <li><strong>配置文件:</strong> backend/config.py 中的全局配置</li>
                        </ul>
                    </div>
                </div>
                """

                # 生成示例配置JSON
                example_json = json.dumps(config_info['example_config'], indent=2, ensure_ascii=False)

                return html, example_json

            except Exception as e:
                return f"<div style='color: red;'>❌ 获取配置失败: {str(e)}</div>", ""

        config_tool_dropdown.change(
            fn=show_tool_config,
            inputs=[config_tool_dropdown],
            outputs=[current_config_display, config_params_input]
        )

        # 保存配置事件
        def save_tool_config(tool_name_with_prefix, config_params_str):
            try:
                if not tool_name_with_prefix:
                    return "⚠️ 请选择要配置的工具"

                if not config_params_str.strip():
                    return "⚠️ 请输入配置参数"

                # 提取工具名称（去掉前缀）
                tool_name = tool_name_with_prefix.split(' ', 1)[1] if ' ' in tool_name_with_prefix else tool_name_with_prefix

                # 解析JSON参数
                try:
                    config_params = json.loads(config_params_str)
                except json.JSONDecodeError as e:
                    return f"❌ JSON格式错误: {str(e)}"

                # 这里可以添加实际的保存逻辑
                # 目前先模拟保存成功
                logger.info(f"保存工具配置: {tool_name} -> {config_params}")

                return f"✅ 工具 {tool_name} 配置已保存\n\n配置内容:\n```json\n{json.dumps(config_params, indent=2, ensure_ascii=False)}\n```\n\n**注意**: 当前为演示模式，实际配置需要在后端文件中修改。"

            except Exception as e:
                return f"❌ 保存配置失败: {str(e)}"

        save_config_btn.click(
            fn=save_tool_config,
            inputs=[config_tool_dropdown, config_params_input],
            outputs=[current_config_display]
        )

    def create_sessions_page(self):
        """创建会话管理页面"""
        gr.Markdown("## 📝 会话管理")
        gr.Markdown("*查看和管理历史对话会话*")

        with gr.Row():
            refresh_sessions_btn = gr.Button("🔄 刷新会话列表", variant="secondary")
            delete_all_btn = gr.Button("🗑️ 删除所有会话", variant="stop")

        # 会话列表显示
        sessions_display = gr.JSON(label="会话列表", value=[])

        # 会话详情显示
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 📖 会话详情")
                session_id_input = gr.Textbox(label="会话ID", placeholder="输入要查看的会话ID")
                view_session_btn = gr.Button("📖 查看会话", variant="primary")

            with gr.Column():
                session_detail_display = gr.JSON(label="会话详情", value={})

        # 事件绑定
        refresh_sessions_btn.click(
            fn=self.get_sessions_list,
            outputs=[sessions_display]
        )

        view_session_btn.click(
            fn=self.get_session_detail,
            inputs=[session_id_input],
            outputs=[session_detail_display]
        )

    def create_developer_page(self):
        """创建开发者模式页面"""
        gr.Markdown("## 🔍 开发者模式")
        gr.Markdown("*学习LangChain的chain、agent、langgraph模式 - 查看实际代码执行过程和AI响应详情*")
        gr.Markdown("*支持最新LangChain 2025特性：原生工具、内置工具、MCP工具集成*")

        with gr.Row():
            refresh_info_btn = gr.Button("🔄 刷新信息", variant="secondary")
            test_agent_btn = gr.Button("🧪 测试当前Agent", variant="primary")

        # 开发者模式标签页
        with gr.Tabs():
            # 工具架构分析
            with gr.TabItem("🔧 工具架构分析"):
                gr.Markdown("### 🏗️ LangChain 2025 工具架构")
                gr.Markdown("*查看当前项目的三层工具架构：原生工具、内置工具、MCP工具*")

                with gr.Row():
                    refresh_tools_arch_btn = gr.Button("🔄 刷新工具架构", variant="secondary")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 🏠 内置工具 (Builtin Tools)")
                        gr.Markdown("*LangChain官方提供的内置工具*")
                        builtin_tools_arch_display = gr.Code(
                            label="内置工具详情",
                            language="json",
                            value="点击刷新获取数据...",
                            lines=8
                        )

                        gr.Markdown("#### 🔧 自定义工具 (Custom Tools)")
                        gr.Markdown("*用户编写的自定义工具*")
                        custom_tools_arch_display = gr.Code(
                            label="自定义工具详情",
                            language="json",
                            value="点击刷新获取数据...",
                            lines=8
                        )

                    with gr.Column():
                        gr.Markdown("#### 🔗 MCP工具 (Model Context Protocol)")
                        gr.Markdown("*支持MCP标准的工具框架*")
                        mcp_tools_arch_display = gr.Code(
                            label="MCP工具详情",
                            language="json",
                            value="点击刷新获取数据...",
                            lines=8
                        )

                        gr.Markdown("#### 📊 工具统计概览")
                        tools_stats_display = gr.Code(
                            label="工具统计信息",
                            language="json",
                            value="点击刷新获取数据...",
                            lines=8
                        )

            # 实时交互追踪
            with gr.TabItem("🔍 实时交互追踪"):
                gr.Markdown("### 📡 最新交互详情")
                gr.Markdown("*在聊天页面发送消息后，这里会显示详细的源码级交互信息*")

                with gr.Row():
                    refresh_interaction_btn = gr.Button("🔄 刷新交互信息", variant="secondary")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 📤 API调用详情")
                        api_call_display = gr.Code(
                            label="API调用信息",
                            language="json",
                            value="等待交互数据...",
                            lines=10
                        )

                        gr.Markdown("#### ⚡ 性能指标")
                        performance_display = gr.Code(
                            label="性能统计",
                            language="json",
                            value="等待交互数据...",
                            lines=6
                        )

                    with gr.Column():
                        gr.Markdown("#### 📥 原始响应对象")
                        raw_response_display = gr.Code(
                            label="完整响应对象",
                            language="json",
                            value="等待交互数据...",
                            lines=16
                        )

                # 用户-AI交互学习区域
                gr.Markdown("### 🎓 用户-AI交互学习")
                gr.Markdown("了解用户消息如何被处理，AI如何生成回复，以及工具如何被调用")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 💬 消息处理流程")
                        interaction_flow_display = gr.Code(
                            label="用户输入 → AI处理 → 工具调用 → 最终回复",
                            language="json",
                            value="发送消息后查看完整的交互流程...",
                            lines=12
                        )

                    with gr.Column():
                        gr.Markdown("#### 🔧 LangChain内部调用")
                        langchain_calls_display = gr.Code(
                            label="LangChain方法和函数调用链",
                            language="python",
                            value="等待交互数据...",
                            lines=12
                        )

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 🔧 执行步骤")
                        execution_steps_display = gr.Textbox(
                            label="详细执行流程",
                            value="等待交互数据...",
                            lines=8,
                            max_lines=15
                        )

                    with gr.Column():
                        gr.Markdown("#### 🧠 思维过程")
                        thinking_display = gr.Textbox(
                            label="AI思维链",
                            value="等待交互数据...",
                            lines=8,
                            max_lines=15
                        )

                # 新增：详细的函数调用和执行流程追踪
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 🔍 函数调用链")
                        function_calls_display = gr.Code(
                            label="函数调用详情",
                            language="json",
                            value="等待交互数据...",
                            lines=10
                        )

                        gr.Markdown("#### 🔄 执行流程追踪")
                        execution_flow_display = gr.Code(
                            label="详细执行流程",
                            language="json",
                            value="等待交互数据...",
                            lines=8
                        )

                    with gr.Column():
                        gr.Markdown("#### 🌐 后端API调用")
                        backend_calls_display = gr.Code(
                            label="后端调用详情",
                            language="json",
                            value="等待交互数据...",
                            lines=10
                        )

                        gr.Markdown("#### 🤖 模型交互记录")
                        model_interactions_display = gr.Code(
                            label="模型交互详情",
                            language="json",
                            value="等待交互数据...",
                            lines=8
                        )

            # Agent架构分析
            with gr.TabItem("🏗️ Agent架构分析"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 🤖 当前Agent信息")
                        current_agent_display = gr.HTML(value="<p>点击刷新获取Agent信息</p>")

                    with gr.Column():
                        gr.Markdown("### 📊 Agent对比")
                        agent_comparison_display = gr.HTML(value="<p>Chain vs Agent vs LangGraph对比</p>")

            # 代码执行追踪
            with gr.TabItem("💻 代码执行追踪"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 🔍 执行流程")
                        execution_flow_display = gr.HTML(value="<p>发送消息查看执行流程</p>")

                    with gr.Column():
                        gr.Markdown("### 📝 代码片段")
                        code_snippets_display = gr.HTML(value="<p>显示关键代码执行片段</p>")

            # AI响应分析
            with gr.TabItem("🧠 AI响应分析"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 📤 最近响应详情")
                        test_message_input = gr.Textbox(
                            label="测试消息",
                            placeholder="输入测试消息查看详细响应过程",
                            lines=2
                        )

                    with gr.Column():
                        gr.Markdown("### 📋 响应对象详情")
                        response_details_display = gr.HTML(value="<p>等待测试消息...</p>")

            # 工具调用分析
            with gr.TabItem("🔧 工具调用分析"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 🛠️ 工具调用链")
                        tool_chain_display = gr.HTML(value="<p>发送需要工具的消息查看调用链</p>")

                    with gr.Column():
                        gr.Markdown("### 📊 工具性能")
                        tool_performance_display = gr.HTML(value="<p>工具执行性能统计</p>")

            # 系统状态
            with gr.TabItem("⚙️ 系统状态"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 🔧 系统信息")
                        system_info_display = gr.HTML(value="<p>点击刷新获取系统信息</p>")

                    with gr.Column():
                        gr.Markdown("### 📋 内存使用")
                        memory_info_display = gr.HTML(value="<p>内存和会话状态</p>")

        # 事件绑定
        async def refresh_all_info():
            try:
                # 获取Agent信息
                agent_info = await self.get_agent_info()
                current_agent_html = self._format_agent_info_html(agent_info)

                # 生成Agent对比
                comparison_html = self._generate_agent_comparison_html()

                # 获取系统信息
                system_html = self._format_system_info_html()

                # 获取内存信息
                memory_html = self._format_memory_info_html()

                return current_agent_html, comparison_html, system_html, memory_html
            except Exception as e:
                error_html = f"<div style='color: red;'>❌ 刷新失败: {str(e)}</div>"
                return error_html, error_html, error_html, error_html

        refresh_info_btn.click(
            fn=refresh_all_info,
            outputs=[current_agent_display, agent_comparison_display, system_info_display, memory_info_display]
        )

        # 刷新交互信息功能
        def refresh_interaction_info():
            try:
                if not self.latest_interaction["timestamp"]:
                    empty_msg = "暂无交互数据，请先在聊天页面发送消息"
                    return (
                        empty_msg, empty_msg, empty_msg, empty_msg, empty_msg,
                        empty_msg, empty_msg, empty_msg, empty_msg
                    )

                # API调用详情
                api_info = {
                    "timestamp": self.latest_interaction["timestamp"],
                    "user_message": self.latest_interaction["user_message"],
                    "api_call_details": self.latest_interaction["api_call_details"],
                    "model_info": self.latest_interaction["model_info"]
                }
                api_call_json = json.dumps(api_info, indent=2, ensure_ascii=False)

                # 性能指标
                performance_json = json.dumps(
                    self.latest_interaction["performance_metrics"],
                    indent=2,
                    ensure_ascii=False
                )

                # 原始响应对象
                raw_response_json = json.dumps(
                    self.latest_interaction["raw_response"],
                    indent=2,
                    ensure_ascii=False
                )

                # 执行步骤
                execution_steps = "\n".join(self.latest_interaction["execution_steps"])

                # 思维过程
                thinking_process = self.latest_interaction["thinking_process"] or "无思维过程记录"

                # LangChain 特定信息
                dev_info = self.latest_interaction.get("dev_info", {})

                # LangChain消息流
                langchain_messages_json = json.dumps(
                    dev_info.get("messages", []),
                    indent=2,
                    ensure_ascii=False
                )

                # 函数调用链
                function_calls_list = dev_info.get("function_calls", [])
                function_calls_text = "\n".join([f"• {func}" for func in function_calls_list])

                # 工具交互过程
                tool_interactions_json = json.dumps(
                    dev_info.get("tool_interactions", []),
                    indent=2,
                    ensure_ascii=False
                )

                # 处理步骤
                processing_steps_list = dev_info.get("processing_steps", [])
                processing_steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(processing_steps_list)])

                # 新增：执行流程追踪
                execution_flow_json = json.dumps(
                    self.latest_interaction["execution_flow"],
                    indent=2,
                    ensure_ascii=False
                )

                # 新增：后端API调用
                backend_calls_json = json.dumps(
                    self.latest_interaction["backend_calls"],
                    indent=2,
                    ensure_ascii=False
                )

                # 新增：模型交互记录
                model_interactions_json = json.dumps(
                    self.latest_interaction["model_interactions"],
                    indent=2,
                    ensure_ascii=False
                )

                # 构建简化的交互流程
                interaction_flow = {
                    "user_input": self.latest_interaction.get("user_message", ""),
                    "ai_processing": {
                        "agent_type": self.latest_interaction.get("agent_type", ""),
                        "model": self.latest_interaction.get("model_info", {}),
                        "thinking_time": self.latest_interaction.get("performance_metrics", {}).get("total_time", 0)
                    },
                    "tool_calls": dev_info.get("tool_interactions", []),
                    "final_response": self.latest_interaction.get("raw_response", {}).get("content", "")
                }

                interaction_flow_json = json.dumps(interaction_flow, indent=2, ensure_ascii=False)

                return (
                    api_call_json,
                    performance_json,
                    raw_response_json,
                    interaction_flow_json,
                    function_calls_text,
                    execution_steps,
                    thinking_process,
                    execution_flow_json,
                    backend_calls_json,
                    model_interactions_json
                )

            except Exception as e:
                error_msg = f"刷新失败: {str(e)}"
                return (error_msg,) * 10

        refresh_interaction_btn.click(
            fn=refresh_interaction_info,
            outputs=[
                api_call_display,
                performance_display,
                raw_response_display,
                interaction_flow_display,
                langchain_calls_display,
                execution_steps_display,
                thinking_display,
                execution_flow_display,
                backend_calls_display,
                model_interactions_display
            ]
        )

        # 工具架构刷新事件
        def refresh_tools_architecture():
            try:
                tools_detail = self.get_tools_info()

                # 内置工具详情
                builtin_tools = tools_detail.get('builtin_tools', [])
                builtin_tools_json = json.dumps(builtin_tools, indent=2, ensure_ascii=False)

                # 自定义工具详情
                custom_tools = tools_detail.get('custom_tools', [])
                custom_tools_json = json.dumps(custom_tools, indent=2, ensure_ascii=False)

                # MCP工具详情
                mcp_tools = tools_detail.get('mcp_tools', [])
                mcp_tools_json = json.dumps(mcp_tools, indent=2, ensure_ascii=False)

                # 工具统计
                stats = {
                    "total_tools": tools_detail.get('total_count', 0),
                    "builtin_count": len(builtin_tools),
                    "custom_count": len(custom_tools),
                    "mcp_count": len(mcp_tools),
                    "architecture": "三层工具架构",
                    "langchain_version": "2025支持",
                    "mcp_support": "已集成",
                    "tool_categories": {
                        "内置工具": {
                            "计算工具": ["calculator", "python_calculator"],
                            "文件工具": ["list_files", "read_file", "get_file_info"],
                            "系统工具": ["system_info", "safe_shell_exec"],
                            "代码工具": ["python_repl_tool", "safe_python_exec"],
                            "数据库工具": ["sql_query", "list_tables", "describe_table"],
                            "搜索工具": ["web_search", "local_search"]
                        },
                        "自定义工具": {
                            "演示工具": ["demo_custom_tool", "weather_tool", "random_quote_tool"],
                            "文本处理": ["text_analyzer_tool", "text_formatter_tool", "text_search_replace_tool"]
                        },
                        "MCP工具": ["mcp_placeholder_tool"]
                    }
                }
                stats_json = json.dumps(stats, indent=2, ensure_ascii=False)

                return builtin_tools_json, custom_tools_json, mcp_tools_json, stats_json

            except Exception as e:
                error_msg = f"刷新工具架构失败: {str(e)}"
                return error_msg, error_msg, error_msg, error_msg

        refresh_tools_arch_btn.click(
            fn=refresh_tools_architecture,
            outputs=[
                builtin_tools_arch_display,
                custom_tools_arch_display,
                mcp_tools_arch_display,
                tools_stats_display
            ]
        )

        # 测试Agent事件
        def test_current_agent(test_message):
            try:
                if not test_message.strip():
                    return "<div style='color: orange;'>⚠️ 请输入测试消息</div>"

                # 执行测试并获取详细信息
                result = self._execute_test_with_details(test_message)
                return self._format_response_details_html(result)
            except Exception as e:
                return f"<div style='color: red;'>❌ 测试失败: {str(e)}</div>"

        test_agent_btn.click(
            fn=test_current_agent,
            inputs=[test_message_input],
            outputs=[response_details_display]
        )
    
    def create_interface(self):
        """创建Gradio多页面界面"""
        with gr.Blocks(
            title="🤖 LangChain 实践项目 - Gradio版",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container {
                max-width: none !important;
                padding: 0 !important;
            }
            .chat-container {
                height: 70vh !important;
            }
            .input-container {
                position: sticky !important;
                bottom: 0 !important;
                background: white !important;
                padding: 10px !important;
                border-top: 1px solid #e0e0e0 !important;
            }
            .nav-button {
                margin: 5px !important;
            }
            .page-container {
                min-height: 80vh !important;
            }
            """
        ) as interface:

            gr.Markdown("# 🤖 LangChain 实践项目 - Gradio版")
            gr.Markdown("*完整功能版本：聊天、工具管理、会话管理、开发者模式*")

            # 导航栏
            with gr.Row():
                nav_chat = gr.Button("💬 聊天", variant="primary", elem_classes=["nav-button"])
                nav_tools = gr.Button("🔧 工具管理", variant="secondary", elem_classes=["nav-button"])
                nav_sessions = gr.Button("📝 会话管理", variant="secondary", elem_classes=["nav-button"])
                nav_developer = gr.Button("🔍 开发者模式", variant="secondary", elem_classes=["nav-button"])

            # 页面容器
            with gr.Column(elem_classes=["page-container"]) as page_container:

                # 聊天页面
                with gr.Column(visible=True) as chat_page:
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("## ⚙️ 配置选项")

                            agent_type = gr.Dropdown(
                                choices=["langchain_core", "chain", "agent", "langgraph", "adaptive", "langchain_native"],
                                value="langchain_core",
                                label="🤖 Agent类型"
                            )

                            # 动态获取模型供应商
                            supported_providers = self.get_supported_providers()
                            current_config = self.get_current_model_config()

                            model_provider = gr.Dropdown(
                                choices=supported_providers,
                                value=current_config.get("provider", supported_providers[0] if supported_providers else "ollama"),
                                label="🔧 模型提供商"
                            )

                            # 动态获取模型列表
                            initial_provider = current_config.get("provider", supported_providers[0] if supported_providers else "ollama")
                            initial_models = self.get_provider_models(initial_provider)

                            model_name = gr.Dropdown(
                                choices=initial_models,
                                value=current_config.get("model", initial_models[0] if initial_models else "qwen2.5:7b"),
                                label="🧠 模型名称",
                                allow_custom_value=True
                            )

                            stream_mode = gr.Checkbox(
                                value=True,
                                label="🔄 启用流式输出"
                            )

                            config_status = gr.Textbox(
                                value="等待配置更新...",
                                label="📊 配置状态",
                                interactive=False
                            )

                            update_config_btn = gr.Button("🔄 更新配置", variant="secondary")
                            clear_btn = gr.Button("🗑️ 清空对话", variant="stop")
                            break_context_btn = gr.Button("✂️ 切断上下文", variant="secondary")

                        with gr.Column(scale=3):
                            gr.Markdown("## 💬 对话区域")

                            chatbot = gr.Chatbot(
                                value=[],
                                height=600,
                                show_label=False,
                                container=True,
                                render_markdown=True,
                                elem_classes=["chat-container"],
                                type="messages"
                            )

                            with gr.Row(elem_classes=["input-container"]):
                                msg_input = gr.Textbox(
                                    placeholder="💬 输入您的问题...",
                                    show_label=False,
                                    scale=4,
                                    container=False
                                )
                                send_btn = gr.Button("📤 发送", variant="primary", scale=1)

                # 工具管理页面
                with gr.Column(visible=False) as tools_page:
                    self.create_tools_page()

                # 会话管理页面
                with gr.Column(visible=False) as sessions_page:
                    self.create_sessions_page()

                # 开发者模式页面
                with gr.Column(visible=False) as developer_page:
                    self.create_developer_page()
            
            # ==================== 事件绑定 ====================

            # 模型供应商变化时更新模型列表
            def update_model_list(provider):
                models = self.get_provider_models(provider)
                return gr.update(choices=models, value=models[0] if models else "")

            model_provider.change(
                fn=update_model_list,
                inputs=[model_provider],
                outputs=[model_name]
            )

            # 页面切换事件
            def switch_to_chat():
                return [gr.update(visible=True), gr.update(visible=False),
                       gr.update(visible=False), gr.update(visible=False)]

            def switch_to_tools():
                return [gr.update(visible=False), gr.update(visible=True),
                       gr.update(visible=False), gr.update(visible=False)]

            def switch_to_sessions():
                return [gr.update(visible=False), gr.update(visible=False),
                       gr.update(visible=True), gr.update(visible=False)]

            def switch_to_developer():
                return [gr.update(visible=False), gr.update(visible=False),
                       gr.update(visible=False), gr.update(visible=True)]

            nav_chat.click(
                fn=switch_to_chat,
                outputs=[chat_page, tools_page, sessions_page, developer_page]
            )

            nav_tools.click(
                fn=switch_to_tools,
                outputs=[chat_page, tools_page, sessions_page, developer_page]
            )

            nav_sessions.click(
                fn=switch_to_sessions,
                outputs=[chat_page, tools_page, sessions_page, developer_page]
            )

            nav_developer.click(
                fn=switch_to_developer,
                outputs=[chat_page, tools_page, sessions_page, developer_page]
            )

            # 聊天页面事件
            update_config_btn.click(
                fn=self.update_agent_config,
                inputs=[agent_type, model_provider, model_name, stream_mode],
                outputs=[config_status]
            )

            clear_btn.click(
                fn=self.clear_chat,
                outputs=[chatbot]
            )

            def break_context_wrapper(current_chatbot_history):
                separator = self.break_context()
                # 在当前聊天历史中添加分隔符，保留之前的对话
                if current_chatbot_history is None:
                    current_chatbot_history = []

                # 添加分隔符到聊天历史 - 使用正确的Gradio格式
                updated_history = current_chatbot_history.copy()
                updated_history.append({
                    "role": "assistant",
                    "content": separator
                })
                return updated_history

            break_context_btn.click(
                fn=break_context_wrapper,
                inputs=[chatbot],
                outputs=[chatbot]
            )

            # 发送消息事件
            send_btn.click(
                fn=self.process_message,
                inputs=[msg_input, chatbot],
                outputs=[chatbot, msg_input],
                show_progress=True
            )

            # 回车发送
            msg_input.submit(
                fn=self.process_message,
                inputs=[msg_input, chatbot],
                outputs=[chatbot, msg_input],
                show_progress=True
            )



        return interface

def main():
    """主函数"""
    app = GradioLangChainApp()
    
    # 初始化后端API
    print("🚀 正在初始化后端API...")
    asyncio.run(agent_api.initialize())
    print("✅ 后端API初始化完成")
    
    # 创建并启动界面
    interface = app.create_interface()
    
    print("🌟 启动Gradio界面...")
    # 尝试不同的端口
    import socket

    def find_free_port(start_port=7860, max_attempts=10):
        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
        return start_port  # 如果都被占用，返回默认端口

    free_port = find_free_port()
    print(f"🌐 使用端口: {free_port}")

    interface.launch(
        server_name="0.0.0.0",
        server_port=free_port,
        share=False,
        debug=True,
        show_error=True
    )

if __name__ == "__main__":
    main()
