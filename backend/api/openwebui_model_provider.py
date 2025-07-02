"""
OpenWebUI模型提供者
为OpenWebUI提供Agent模式和模型分离的自定义模型
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
import logging
import httpx

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_ollama_models():
    """获取Ollama可用模型"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://host.docker.internal:11434/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
    except Exception as e:
        logger.warning(f"Failed to get Ollama models: {e}")
    
    # 返回默认模型列表
    return [
        {"name": "qwen2.5:7b", "size": 4000000000},
        {"name": "qwen2.5:14b", "size": 8000000000},
        {"name": "llama3.1:8b", "size": 5000000000},
        {"name": "mistral:7b", "size": 4000000000}
    ]


@router.get("/api/models")
async def get_openwebui_models():
    """
    为OpenWebUI提供模型列表
    包含Agent模式和模型的组合
    """
    try:
        models = []
        
        # 获取Ollama模型
        ollama_models = await get_ollama_models()
        
        # Agent模式定义
        agent_modes = {
            "chain": {
                "name": "Chain Agent",
                "description": "基于Runnable接口的简单Agent，适合日常对话",
                "icon": "🔗"
            },
            "agent": {
                "name": "Tool Agent", 
                "description": "支持工具调用的智能Agent，适合复杂任务",
                "icon": "🛠️"
            },
            "langgraph": {
                "name": "Graph Agent",
                "description": "基于状态图的高级Agent，适合复杂工作流",
                "icon": "🕸️"
            }
        }
        
        # 为每个Agent模式和模型组合创建模型条目
        for mode_id, mode_info in agent_modes.items():
            for ollama_model in ollama_models:
                model_name = ollama_model.get("name", "")
                model_size = ollama_model.get("size", 0)
                
                # 计算模型大小
                size_gb = f"{model_size / 1000000000:.1f}GB" if model_size > 0 else ""
                
                # 构建模型ID和显示名称
                model_id = f"langchain-{mode_id}-{model_name.replace(':', '-')}"
                display_name = f"{mode_info['icon']} {mode_info['name']} + {model_name}"
                if size_gb:
                    display_name += f" ({size_gb})"
                
                models.append({
                    "id": model_id,
                    "name": display_name,
                    "object": "model",
                    "created": 1699000000,
                    "owned_by": "langchain",
                    "permission": [],
                    "root": model_id,
                    "parent": None,
                    "description": f"{mode_info['description']} - 使用 {model_name} 模型",
                    "metadata": {
                        "agent_mode": mode_id,
                        "ollama_model": model_name,
                        "type": "agent_combo"
                    }
                })
        
        # 添加Agent配置器
        models.append({
            "id": "langchain-configurator",
            "name": "🔧 Agent配置器",
            "object": "model",
            "created": 1699000000,
            "owned_by": "langchain",
            "permission": [],
            "root": "langchain-configurator",
            "parent": None,
            "description": "配置和管理Agent模式与模型",
            "metadata": {
                "agent_mode": "config",
                "ollama_model": "none",
                "type": "configurator"
            }
        })
        
        return {"data": models}
        
    except Exception as e:
        logger.error(f"Failed to get OpenWebUI models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/chat/completions")
async def handle_chat_completions(request: Dict[str, Any]):
    """
    处理OpenWebUI的聊天完成请求
    根据模型ID路由到相应的Agent
    """
    try:
        model_id = request.get("model", "")
        messages = request.get("messages", [])
        
        # 处理配置器请求
        if model_id == "langchain-configurator":
            return await handle_configurator_request(messages, request)
        
        # 处理Agent组合请求
        if model_id.startswith("langchain-") and "-" in model_id:
            return await handle_agent_combo_request(model_id, request)
        
        # 默认处理
        return {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1699000000,
            "model": model_id,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"未知模型: {model_id}"
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error handling chat completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_configurator_request(messages: List[Dict], request: Dict[str, Any]):
    """处理配置器请求"""
    try:
        if not messages:
            content = get_configurator_help()
        else:
            last_message = messages[-1].get("content", "").lower()
            
            if "列出模式" in last_message or "list modes" in last_message:
                content = await get_agent_modes_info()
            elif "列出模型" in last_message or "list models" in last_message:
                content = await get_ollama_models_info()
            elif "配置" in last_message:
                content = await handle_configuration_command(last_message)
            elif "状态" in last_message or "status" in last_message:
                content = await get_agent_status()
            else:
                content = get_configurator_help()
        
        return {
            "id": "chatcmpl-config",
            "object": "chat.completion",
            "created": 1699000000,
            "model": "langchain-configurator",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(str(messages)),
                "completion_tokens": len(content),
                "total_tokens": len(str(messages)) + len(content)
            }
        }
        
    except Exception as e:
        logger.error(f"Error handling configurator request: {e}")
        return {
            "id": "chatcmpl-error",
            "object": "chat.completion",
            "created": 1699000000,
            "model": "langchain-configurator",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"配置器错误: {str(e)}"
                },
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }


async def handle_agent_combo_request(model_id: str, request: Dict[str, Any]):
    """处理Agent组合请求"""
    try:
        # 解析模型ID
        parts = model_id.replace("langchain-", "").split("-", 1)
        if len(parts) < 2:
            raise ValueError(f"Invalid model ID: {model_id}")
        
        agent_mode = parts[0]
        ollama_model = parts[1].replace("-", ":")
        
        # 配置Agent
        await configure_agent_backend(agent_mode, ollama_model)
        
        # 转发请求到LangChain后端
        backend_model = f"langchain-{agent_mode}-mode"
        backend_request = {**request, "model": backend_model}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://langchain-backend:8000/v1/chat/completions",
                json=backend_request,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)
                
    except Exception as e:
        logger.error(f"Error handling agent combo request: {e}")
        return {
            "id": "chatcmpl-error",
            "object": "chat.completion",
            "created": 1699000000,
            "model": model_id,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"Agent请求错误: {str(e)}"
                },
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }


async def configure_agent_backend(mode: str, model: str):
    """配置Agent后端"""
    try:
        payload = {"mode": mode, "model": model}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://langchain-backend:8000/v1/agent/configure",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully configured {mode} agent with {model} model")
            else:
                logger.warning(f"Failed to configure agent: {response.status_code}")
                
    except Exception as e:
        logger.error(f"Error configuring agent: {e}")


def get_configurator_help():
    """获取配置器帮助信息"""
    return """
🎯 LangChain Agent配置器

**使用方法:**
1. 在模型列表中选择Agent模式和模型的组合
2. 系统会自动配置相应的Agent
3. 开始对话！

**可用命令:**
• "列出模式" - 查看所有Agent模式
• "列出模型" - 查看所有Ollama模型
• "配置chain Agent使用qwen2.5:7b模型" - 手动配置
• "获取状态" - 查看当前配置

**Agent模式:**
🔗 **Chain Agent** - 适合日常对话和简单任务
🛠️ **Tool Agent** - 适合工具调用和复杂任务  
🕸️ **Graph Agent** - 适合复杂工作流和状态管理

**快速开始:**
直接从模型列表中选择想要的Agent模式和模型组合即可！
"""


async def get_agent_modes_info():
    """获取Agent模式信息"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://langchain-backend:8000/v1/agent/modes", timeout=10)
            if response.status_code == 200:
                data = response.json()
                modes = data.get("modes", {})
                
                result = "🤖 可用的Agent模式:\n\n"
                for mode_id, mode_info in modes.items():
                    result += f"**{mode_info['name']}** ({mode_id})\n"
                    result += f"描述: {mode_info['description']}\n"
                    result += f"特性: {', '.join(mode_info['features'])}\n\n"
                
                return result
            else:
                return f"❌ 获取Agent模式失败: {response.status_code}"
    except Exception as e:
        return f"❌ 请求异常: {e}"


async def get_ollama_models_info():
    """获取Ollama模型信息"""
    try:
        models = await get_ollama_models()
        result = "🧠 可用的Ollama模型:\n\n"
        for model in models:
            name = model.get("name", "")
            size = model.get("size", 0)
            size_gb = f"{size / 1000000000:.1f}GB" if size > 0 else "未知大小"
            result += f"• **{name}** ({size_gb})\n"
        return result
    except Exception as e:
        return f"❌ 获取模型失败: {e}"


async def handle_configuration_command(command: str):
    """处理配置命令"""
    # 简单的配置解析
    if "chain" in command:
        mode = "chain"
    elif "agent" in command:
        mode = "agent"
    elif "langgraph" in command or "graph" in command:
        mode = "langgraph"
    else:
        return "❌ 请指定Agent模式 (chain, agent, langgraph)"
    
    # 提取模型名称
    model = None
    if "qwen2.5:7b" in command:
        model = "qwen2.5:7b"
    elif "qwen2.5:14b" in command:
        model = "qwen2.5:14b"
    elif "llama3.1:8b" in command:
        model = "llama3.1:8b"
    elif "mistral:7b" in command:
        model = "mistral:7b"
    
    if not model:
        return f"❌ 请指定模型名称，例如: 配置{mode} Agent使用qwen2.5:7b模型"
    
    try:
        await configure_agent_backend(mode, model)
        return f"✅ 配置成功！{mode} Agent 现在使用 {model} 模型"
    except Exception as e:
        return f"❌ 配置失败: {e}"


async def get_agent_status():
    """获取Agent状态"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://langchain-backend:8000/v1/agent/current-config", timeout=10)
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
