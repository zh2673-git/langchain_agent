"""
LangChain Agent Pipe for OpenWebUI
创建Agent模式和模型分离的自定义模型选择器
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
        ENABLE_AGENT_MODES: bool = Field(
            default=True,
            description="启用Agent模式选择"
        )
        SHOW_MODEL_INFO: bool = Field(
            default=True,
            description="在模型名称中显示详细信息"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.agent_modes = {
            "chain": {
                "name": "Chain Agent",
                "description": "基于Runnable接口的简单Agent，适合日常对话",
                "icon": "🔗",
                "features": ["快速响应", "简单对话", "基础工具调用"]
            },
            "agent": {
                "name": "Tool Agent", 
                "description": "支持工具调用的智能Agent，适合复杂任务",
                "icon": "🛠️",
                "features": ["工具调用", "推理能力", "多步骤任务"]
            },
            "langgraph": {
                "name": "Graph Agent",
                "description": "基于状态图的高级Agent，适合复杂工作流",
                "icon": "🕸️",
                "features": ["状态管理", "复杂工作流", "条件分支"]
            }
        }

    def get_ollama_models(self) -> List[Dict]:
        """获取Ollama可用模型"""
        try:
            response = requests.get(f"{self.valves.OLLAMA_URL}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
        except Exception as e:
            print(f"Failed to get Ollama models: {e}")
        
        # 返回默认模型列表
        return [
            {"name": "qwen2.5:7b", "size": 4000000000},
            {"name": "qwen2.5:14b", "size": 8000000000},
            {"name": "llama3.1:8b", "size": 5000000000},
            {"name": "mistral:7b", "size": 4000000000}
        ]

    def pipes(self) -> List[Dict]:
        """返回可用的模型列表（Agent模式 + 模型组合）"""
        if not self.valves.ENABLE_AGENT_MODES:
            return []

        models = []
        ollama_models = self.get_ollama_models()
        
        # 为每个Agent模式创建模型选项
        for mode_id, mode_info in self.agent_modes.items():
            for ollama_model in ollama_models:
                model_name = ollama_model.get("name", "")
                model_size = ollama_model.get("size", 0)
                
                # 计算模型大小
                size_gb = f"{model_size / 1000000000:.1f}GB" if model_size > 0 else ""
                
                # 构建模型ID和显示名称
                model_id = f"langchain-{mode_id}-{model_name.replace(':', '-')}"
                
                if self.valves.SHOW_MODEL_INFO:
                    display_name = f"{mode_info['icon']} {mode_info['name']} + {model_name}"
                    if size_gb:
                        display_name += f" ({size_gb})"
                else:
                    display_name = f"{mode_info['name']} ({model_name})"
                
                models.append({
                    "id": model_id,
                    "name": display_name,
                    "description": f"{mode_info['description']} - 使用 {model_name} 模型",
                    "metadata": {
                        "agent_mode": mode_id,
                        "ollama_model": model_name,
                        "features": mode_info["features"]
                    }
                })
        
        # 添加模式选择器（用于配置）
        models.append({
            "id": "langchain-config",
            "name": "🔧 Agent配置器",
            "description": "配置和管理Agent模式与模型",
            "metadata": {
                "agent_mode": "config",
                "ollama_model": "none"
            }
        })
        
        return models

    async def pipe(self, body: dict, __user__: dict = None) -> str:
        """处理请求并转发到相应的Agent"""
        try:
            model_id = body.get("model", "")
            messages = body.get("messages", [])
            
            # 解析模型ID
            if model_id == "langchain-config":
                return await self.handle_config_request(messages)
            
            if not model_id.startswith("langchain-"):
                return "错误：无效的模型ID"
            
            # 提取Agent模式和Ollama模型
            parts = model_id.replace("langchain-", "").split("-", 1)
            if len(parts) < 2:
                return "错误：无法解析模型ID"
            
            agent_mode = parts[0]
            ollama_model = parts[1].replace("-", ":")
            
            # 配置Agent
            await self.configure_agent(agent_mode, ollama_model)
            
            # 转发请求到LangChain后端
            backend_model = f"langchain-{agent_mode}-mode"
            payload = {**body, "model": backend_model}
            
            response = requests.post(
                f"{self.valves.BACKEND_URL}/v1/chat/completions",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return content
            else:
                return f"错误：后端请求失败 ({response.status_code})"
                
        except Exception as e:
            return f"错误：{str(e)}"

    async def configure_agent(self, mode: str, model: str):
        """配置Agent模式和模型"""
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
                print(f"Successfully configured {mode} agent with {model} model")
            else:
                print(f"Failed to configure agent: {response.status_code}")
                
        except Exception as e:
            print(f"Error configuring agent: {e}")

    async def handle_config_request(self, messages: List[Dict]) -> str:
        """处理配置请求"""
        if not messages:
            return self.get_config_help()
        
        last_message = messages[-1].get("content", "").lower()
        
        if "列出" in last_message or "list" in last_message:
            if "模式" in last_message or "mode" in last_message:
                return self.list_agent_modes()
            elif "模型" in last_message or "model" in last_message:
                return self.list_ollama_models()
        
        elif "配置" in last_message or "config" in last_message:
            return self.get_config_instructions()
        
        elif "帮助" in last_message or "help" in last_message:
            return self.get_config_help()
        
        return self.get_config_help()

    def list_agent_modes(self) -> str:
        """列出Agent模式"""
        result = "🤖 可用的Agent模式:\n\n"
        for mode_id, mode_info in self.agent_modes.items():
            result += f"**{mode_info['icon']} {mode_info['name']}** ({mode_id})\n"
            result += f"描述: {mode_info['description']}\n"
            result += f"特性: {', '.join(mode_info['features'])}\n\n"
        return result

    def list_ollama_models(self) -> str:
        """列出Ollama模型"""
        models = self.get_ollama_models()
        result = "🧠 可用的Ollama模型:\n\n"
        for model in models:
            name = model.get("name", "")
            size = model.get("size", 0)
            size_gb = f"{size / 1000000000:.1f}GB" if size > 0 else "未知大小"
            result += f"• **{name}** ({size_gb})\n"
        return result

    def get_config_instructions(self) -> str:
        """获取配置说明"""
        return """
🔧 Agent配置说明:

**自动配置方式:**
直接选择想要的Agent模式和模型组合，系统会自动配置。

**可用组合:**
- 🔗 Chain Agent + 任意Ollama模型
- 🛠️ Tool Agent + 任意Ollama模型  
- 🕸️ Graph Agent + 任意Ollama模型

**推荐配置:**
- 日常对话: Chain Agent + qwen2.5:7b
- 复杂任务: Tool Agent + qwen2.5:14b
- 工作流: Graph Agent + llama3.1:8b

选择模型后，系统会自动配置相应的Agent模式！
"""

    def get_config_help(self) -> str:
        """获取帮助信息"""
        return """
🎯 LangChain Agent配置器

**可用命令:**
- "列出模式" - 查看所有Agent模式
- "列出模型" - 查看所有Ollama模型
- "配置说明" - 查看配置方法
- "帮助" - 显示此帮助信息

**快速开始:**
1. 从模型列表中选择Agent模式和模型组合
2. 系统自动配置相应的Agent
3. 开始对话！

**Agent模式:**
🔗 Chain Agent - 简单对话
🛠️ Tool Agent - 工具调用
🕸️ Graph Agent - 复杂工作流
"""
