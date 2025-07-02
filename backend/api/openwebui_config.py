"""
OpenWebUI配置API
提供OpenWebUI前端所需的配置信息，包括模型切换和工具管理
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/v1/models/config")
async def get_models_config():
    """获取模型配置信息，包括可切换的底层模型"""
    try:
        models_config = {
            "langchain-chain": {
                "id": "langchain-chain",
                "name": "LangChain Chain Agent",
                "description": "基于Runnable接口组合的Chain Agent",
                "agent_type": "chain",
                "supports_tools": True,
                "current_model": "qwen2.5:7b",
                "available_models": [
                    {
                        "id": "qwen2.5:7b",
                        "name": "Qwen2.5 7B",
                        "description": "通义千问2.5 7B模型"
                    },
                    {
                        "id": "qwen2.5:14b", 
                        "name": "Qwen2.5 14B",
                        "description": "通义千问2.5 14B模型"
                    },
                    {
                        "id": "llama3.1:8b",
                        "name": "Llama 3.1 8B", 
                        "description": "Meta Llama 3.1 8B模型"
                    },
                    {
                        "id": "mistral:7b",
                        "name": "Mistral 7B",
                        "description": "Mistral 7B模型"
                    }
                ]
            },
            "langchain-agent": {
                "id": "langchain-agent",
                "name": "LangChain Agent",
                "description": "使用create_tool_calling_agent的Agent",
                "agent_type": "agent", 
                "supports_tools": True,
                "current_model": "qwen2.5:7b",
                "available_models": [
                    {
                        "id": "qwen2.5:7b",
                        "name": "Qwen2.5 7B",
                        "description": "通义千问2.5 7B模型"
                    },
                    {
                        "id": "qwen2.5:14b",
                        "name": "Qwen2.5 14B", 
                        "description": "通义千问2.5 14B模型"
                    },
                    {
                        "id": "llama3.1:8b",
                        "name": "Llama 3.1 8B",
                        "description": "Meta Llama 3.1 8B模型"
                    },
                    {
                        "id": "mistral:7b",
                        "name": "Mistral 7B",
                        "description": "Mistral 7B模型"
                    }
                ]
            },
            "langchain-langgraph": {
                "id": "langchain-langgraph",
                "name": "LangChain LangGraph Agent",
                "description": "使用状态图实现的LangGraph Agent",
                "agent_type": "langgraph",
                "supports_tools": True, 
                "current_model": "qwen2.5:7b",
                "available_models": [
                    {
                        "id": "qwen2.5:7b",
                        "name": "Qwen2.5 7B",
                        "description": "通义千问2.5 7B模型"
                    },
                    {
                        "id": "qwen2.5:14b",
                        "name": "Qwen2.5 14B",
                        "description": "通义千问2.5 14B模型"
                    },
                    {
                        "id": "llama3.1:8b", 
                        "name": "Llama 3.1 8B",
                        "description": "Meta Llama 3.1 8B模型"
                    },
                    {
                        "id": "mistral:7b",
                        "name": "Mistral 7B",
                        "description": "Mistral 7B模型"
                    }
                ]
            }
        }
        
        return {
            "success": True,
            "models": models_config
        }
        
    except Exception as e:
        logger.error(f"Failed to get models config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v1/tools/config")
async def get_tools_config():
    """获取工具配置信息"""
    try:
        from backend.tools.tool_service import get_tool_service

        tool_service = get_tool_service()

        # 确保工具服务已初始化
        if not tool_service.loaded_tools:
            await tool_service.initialize()

        tools = tool_service.get_tools()
        
        tools_config = []
        for tool in tools:
            tool_info = {
                "id": tool.name,
                "name": tool.name,
                "description": tool.description,
                "enabled": True,
                "category": "custom",  # 可以根据工具来源分类
                "parameters": getattr(tool, 'args_schema', None)
            }
            tools_config.append(tool_info)
        
        return {
            "success": True,
            "tools": tools_config,
            "total": len(tools_config)
        }
        
    except Exception as e:
        logger.error(f"Failed to get tools config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v1/models/{model_id}/switch-backend")
async def switch_model_backend(model_id: str, request: Dict[str, Any]):
    """为指定模型切换底层模型"""
    try:
        new_backend_model = request.get("backend_model")
        if not new_backend_model:
            raise HTTPException(status_code=400, detail="Missing backend_model parameter")
        
        # 解析agent类型
        if model_id.startswith("langchain-"):
            agent_type = model_id.replace("langchain-", "")
        else:
            raise HTTPException(status_code=400, detail=f"Invalid model ID: {model_id}")
        
        # 调用现有的模型切换API
        from backend.api.api import AgentAPI
        api = AgentAPI()
        await api.initialize()
        
        success = await api.switch_agent_model(agent_type, new_backend_model)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully switched {model_id} to backend model {new_backend_model}",
                "model_id": model_id,
                "backend_model": new_backend_model
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to switch backend model")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching backend model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v1/config/ui")
async def get_ui_config():
    """获取UI配置信息"""
    try:
        ui_config = {
            "features": {
                "model_switching": True,
                "tool_management": True,
                "agent_selection": True
            },
            "agent_types": [
                {
                    "id": "chain",
                    "name": "Chain Agent",
                    "description": "基于Runnable接口组合"
                },
                {
                    "id": "agent", 
                    "name": "Tool Agent",
                    "description": "支持工具调用的Agent"
                },
                {
                    "id": "langgraph",
                    "name": "Graph Agent", 
                    "description": "基于状态图的复杂Agent"
                }
            ],
            "supported_models": [
                "qwen2.5:7b",
                "qwen2.5:14b", 
                "llama3.1:8b",
                "mistral:7b"
            ]
        }
        
        return {
            "success": True,
            "config": ui_config
        }
        
    except Exception as e:
        logger.error(f"Failed to get UI config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
