"""
Agent工具函数
为OpenWebUI提供Agent配置和管理功能
"""

from pydantic import BaseModel, Field
import requests
import json
from typing import List, Dict, Any


class Pipe:
    class Valves(BaseModel):
        BACKEND_URL: str = Field(
            default="http://langchain-backend:8000",
            description="LangChain后端API地址"
        )
        OLLAMA_URL: str = Field(
            default="http://host.docker.internal:11434", 
            description="Ollama API地址"
        )

    def __init__(self):
        self.valves = self.Valves()

    def pipes(self) -> List[Dict]:
        """返回Agent工具模型"""
        return [
            {
                "id": "agent-tools",
                "name": "🛠️ Agent工具",
                "description": "Agent配置和管理工具"
            }
        ]

    async def pipe(self, body: dict, __user__: dict = None) -> str:
        """处理Agent工具请求"""
        try:
            messages = body.get("messages", [])
            if not messages:
                return self.get_help_message()

            last_message = messages[-1].get("content", "").lower()
            
            if "列出模式" in last_message or "list modes" in last_message:
                return await self.list_agent_modes()
            elif "列出模型" in last_message or "list models" in last_message:
                return await self.list_ollama_models()
            elif "配置" in last_message and ("agent" in last_message or "模式" in last_message):
                return await self.handle_config_request(last_message)
            elif "状态" in last_message or "status" in last_message:
                return await self.get_agent_status()
            elif "推荐" in last_message or "recommend" in last_message:
                return await self.get_recommendations()
            else:
                return self.get_help_message()
                
        except Exception as e:
            return f"错误：{str(e)}"

    async def list_agent_modes(self) -> str:
        """列出Agent模式"""
        try:
            response = requests.get(f"{self.valves.BACKEND_URL}/v1/agent/modes", timeout=10)
            if response.status_code == 200:
                data = response.json()
                modes = data.get("modes", {})
                
                result = "🤖 可用的Agent模式:\n\n"
                for mode_id, mode_info in modes.items():
                    result += f"**{mode_info['name']}** ({mode_id})\n"
                    result += f"描述: {mode_info['description']}\n"
                    result += f"特性: {', '.join(mode_info['features'])}\n"
                    result += f"适用场景: {', '.join(mode_info['use_cases'])}\n\n"
                
                return result
            else:
                return f"❌ 获取Agent模式失败: {response.status_code}"
        except Exception as e:
            return f"❌ 请求异常: {e}"

    async def list_ollama_models(self) -> str:
        """列出Ollama模型"""
        try:
            response = requests.get(f"{self.valves.OLLAMA_URL}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                
                result = "🧠 可用的Ollama模型:\n\n"
                for model in models:
                    name = model.get("name", "")
                    size = model.get("size", 0)
                    size_gb = f"{size / 1000000000:.1f}GB" if size > 0 else "未知大小"
                    result += f"• **{name}** ({size_gb})\n"
                
                return result
            else:
                return f"❌ 获取模型列表失败: {response.status_code}"
        except Exception as e:
            return f"❌ 请求异常: {e}"

    async def handle_config_request(self, message: str) -> str:
        """处理配置请求"""
        # 简单的配置解析
        if "chain" in message:
            mode = "chain"
        elif "agent" in message:
            mode = "agent"
        elif "langgraph" in message or "graph" in message:
            mode = "langgraph"
        else:
            return "❌ 请指定Agent模式 (chain, agent, langgraph)"
        
        # 提取模型名称
        model = None
        if "qwen2.5:7b" in message:
            model = "qwen2.5:7b"
        elif "qwen2.5:14b" in message:
            model = "qwen2.5:14b"
        elif "llama3.1:8b" in message:
            model = "llama3.1:8b"
        elif "mistral:7b" in message:
            model = "mistral:7b"
        elif "qwen3:8b" in message:
            model = "qwen3:8b"
        
        if not model:
            return f"❌ 请指定模型名称，例如: 配置{mode} Agent使用qwen2.5:7b模型"
        
        return await self.configure_agent(mode, model)

    async def configure_agent(self, mode: str, model: str) -> str:
        """配置Agent"""
        try:
            payload = {
                "mode": mode,
                "model": model
            }
            
            response = requests.post(
                f"{self.valves.BACKEND_URL}/v1/agent/configure",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return f"✅ 配置成功！{mode} Agent 现在使用 {model} 模型"
                else:
                    return f"❌ 配置失败: {data.get('message', '未知错误')}"
            else:
                return f"❌ 配置请求失败: {response.status_code}"
                
        except Exception as e:
            return f"❌ 配置异常: {e}"

    async def get_agent_status(self) -> str:
        """获取Agent状态"""
        try:
            response = requests.get(f"{self.valves.BACKEND_URL}/v1/agent/current-config", timeout=10)
            if response.status_code == 200:
                data = response.json()
                config = data.get("current_config", {})
                
                result = "⚙️ 当前Agent配置:\n\n"
                for agent_type, agent_config in config.items():
                    mode = agent_config.get("mode", "")
                    model = agent_config.get("model", "")
                    status = agent_config.get("status", "")
                    result += f"**{agent_type}**: {mode} + {model} ({status})\n"
                
                return result
            else:
                return f"❌ 获取状态失败: {response.status_code}"
        except Exception as e:
            return f"❌ 请求异常: {e}"

    async def get_recommendations(self) -> str:
        """获取推荐配置"""
        try:
            response = requests.get(f"{self.valves.BACKEND_URL}/v1/agent/recommendations", timeout=10)
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get("recommendations", {})
                
                result = "💡 推荐配置:\n\n"
                
                # 任务推荐
                by_task = recommendations.get("by_task", {})
                result += "**按任务类型推荐:**\n"
                for task, rec in by_task.items():
                    mode = rec.get("recommended_mode", "")
                    model = rec.get("recommended_model", "")
                    reason = rec.get("reason", "")
                    result += f"• {task}: {mode} + {model}\n  原因: {reason}\n\n"
                
                return result
            else:
                return f"❌ 获取推荐失败: {response.status_code}"
        except Exception as e:
            return f"❌ 请求异常: {e}"

    def get_help_message(self) -> str:
        """获取帮助信息"""
        return """
🎯 Agent工具使用指南

**可用命令:**
• "列出模式" - 查看所有Agent模式
• "列出模型" - 查看所有Ollama模型  
• "配置chain Agent使用qwen2.5:7b模型" - 配置Agent
• "获取状态" - 查看当前配置
• "获取推荐" - 查看推荐配置

**Agent模式:**
🔗 **Chain Agent** - 适合日常对话和简单任务
🛠️ **Tool Agent** - 适合工具调用和复杂任务
🕸️ **Graph Agent** - 适合复杂工作流和状态管理

**配置示例:**
- "配置chain Agent使用qwen2.5:7b模型"
- "配置agent Agent使用qwen2.5:14b模型"
- "配置langgraph Agent使用llama3.1:8b模型"

**快速开始:**
1. 输入"列出模式"查看可用Agent
2. 输入"列出模型"查看可用模型
3. 选择合适的组合进行配置
4. 切换到相应的Agent模型开始对话！
"""
