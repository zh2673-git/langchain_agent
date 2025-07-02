"""
OpenWebUI模型配置
重新设计模型列表，将Agent模式和模型分离
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_ollama_models():
    """从Ollama获取可用模型"""
    try:
        import httpx
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


@router.get("/v1/models")
async def list_models():
    """
    列出可用模型
    重新设计：动态获取Ollama模型，Agent模式作为虚拟模型
    """
    try:
        models = []

        # 动态获取Ollama模型
        ollama_models = await get_ollama_models()

        # 转换为OpenAI格式的基础模型
        for model in ollama_models:
            model_name = model.get("name", "")
            model_size = model.get("size", 0)

            # 解析模型信息
            provider = "unknown"
            if "qwen" in model_name.lower():
                provider = "Alibaba"
            elif "llama" in model_name.lower():
                provider = "Meta"
            elif "mistral" in model_name.lower():
                provider = "Mistral AI"
            elif "gemma" in model_name.lower():
                provider = "Google"

            size_gb = f"{model_size / 1000000000:.1f}B" if model_size > 0 else "Unknown"

            base_model = {
                "id": model_name,
                "object": "model",
                "created": 1699000000,
                "owned_by": provider.lower(),
                "permission": [],
                "root": model_name,
                "parent": None,
                "description": f"{model_name} - {provider} 模型",
                "capabilities": {
                    "chat": True,
                    "tools": True,
                    "streaming": True
                },
                "metadata": {
                    "size": size_gb,
                    "provider": provider,
                    "type": "base_model",
                    "performance": {
                        "speed": "fast" if model_size < 5000000000 else "medium",
                        "quality": "excellent" if model_size > 7000000000 else "good",
                        "memory": "low" if model_size < 5000000000 else "medium"
                    }
                }
            }
            models.append(base_model)
        
        # 获取可用模型名称列表
        available_model_names = [model.get("name", "") for model in ollama_models]

        # Agent模式模型（虚拟模型，用于模式选择）
        agent_modes = [
            {
                "id": "langchain-chain-mode",
                "object": "model",
                "created": 1699000000,
                "owned_by": "langchain",
                "permission": [],
                "root": "langchain-chain-mode",
                "parent": None,
                "description": "Chain Agent模式 - 基于Runnable接口的简单Agent",
                "capabilities": {
                    "chat": True,
                    "tools": True,
                    "streaming": True,
                    "mode_selection": True
                },
                "metadata": {
                    "type": "agent_mode",
                    "mode": "chain",
                    "current_model": "qwen2.5:7b",
                    "available_models": available_model_names,
                    "features": ["快速响应", "简单对话", "基础工具调用"],
                    "use_cases": ["日常对话", "简单计算", "信息查询"]
                }
            },
            {
                "id": "langchain-agent-mode",
                "object": "model",
                "created": 1699000000,
                "owned_by": "langchain",
                "permission": [],
                "root": "langchain-agent-mode",
                "parent": None,
                "description": "Tool Agent模式 - 支持工具调用的智能Agent",
                "capabilities": {
                    "chat": True,
                    "tools": True,
                    "streaming": True,
                    "mode_selection": True
                },
                "metadata": {
                    "type": "agent_mode",
                    "mode": "agent",
                    "current_model": "qwen2.5:7b",
                    "available_models": available_model_names,
                    "features": ["工具调用", "推理能力", "多步骤任务"],
                    "use_cases": ["数据分析", "文件操作", "复杂计算"]
                }
            },
            {
                "id": "langchain-langgraph-mode",
                "object": "model",
                "created": 1699000000,
                "owned_by": "langchain",
                "permission": [],
                "root": "langchain-langgraph-mode",
                "parent": None,
                "description": "Graph Agent模式 - 基于状态图的高级Agent",
                "capabilities": {
                    "chat": True,
                    "tools": True,
                    "streaming": True,
                    "mode_selection": True
                },
                "metadata": {
                    "type": "agent_mode",
                    "mode": "langgraph",
                    "current_model": "qwen2.5:7b",
                    "available_models": available_model_names,
                    "features": ["状态管理", "复杂工作流", "条件分支"],
                    "use_cases": ["多步骤分析", "决策流程", "复杂业务逻辑"]
                }
            }
        ]

        # 合并所有模型
        models.extend(agent_modes)
        
        return {
            "object": "list",
            "data": models
        }
        
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v1/models/{model_id}")
async def get_model(model_id: str):
    """获取特定模型信息"""
    try:
        # 这里应该根据model_id返回具体的模型信息
        # 暂时返回通用信息
        model_info = {
            "id": model_id,
            "object": "model",
            "created": 1699000000,
            "owned_by": "system",
            "permission": [],
            "root": model_id,
            "parent": None
        }
        
        return model_info
        
    except Exception as e:
        logger.error(f"Failed to get model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v1/models/{model_id}/switch-backend")
async def switch_model_backend(model_id: str, request: Dict[str, Any]):
    """为Agent模式切换底层模型"""
    try:
        backend_model = request.get("backend_model")
        if not backend_model:
            raise HTTPException(status_code=400, detail="Missing backend_model parameter")
        
        # 解析Agent模式
        if model_id.endswith("-mode"):
            mode = model_id.replace("langchain-", "").replace("-mode", "")
        else:
            raise HTTPException(status_code=400, detail=f"Invalid agent mode model: {model_id}")
        
        # 调用Agent配置API
        from .agent_mode_api import configure_agent

        config_request = {
            "mode": mode,
            "model": backend_model
        }

        await configure_agent(config_request)
        
        return {
            "success": True,
            "message": f"Successfully switched {model_id} to backend model {backend_model}",
            "model_id": model_id,
            "backend_model": backend_model
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching backend model: {e}")
        raise HTTPException(status_code=500, detail=str(e))
