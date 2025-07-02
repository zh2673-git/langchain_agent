"""
Agent模式API
将Agent模式和模型分离，提供更灵活的配置方式
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
import logging

from .api import AgentAPI

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/v1/agent/modes")
async def get_agent_modes():
    """获取可用的Agent模式"""
    try:
        modes = {
            "chain": {
                "id": "chain",
                "name": "Chain Agent",
                "description": "基于Runnable接口组合的简单Agent，适合线性任务处理",
                "features": ["快速响应", "简单对话", "基础工具调用"],
                "use_cases": ["日常对话", "简单计算", "信息查询"]
            },
            "agent": {
                "id": "agent",
                "name": "Tool Agent", 
                "description": "支持工具调用的智能Agent，适合复杂任务处理",
                "features": ["工具调用", "推理能力", "多步骤任务"],
                "use_cases": ["数据分析", "文件操作", "复杂计算"]
            },
            "langgraph": {
                "id": "langgraph",
                "name": "Graph Agent",
                "description": "基于状态图的高级Agent，适合复杂工作流",
                "features": ["状态管理", "复杂工作流", "条件分支"],
                "use_cases": ["多步骤分析", "决策流程", "复杂业务逻辑"]
            }
        }
        
        return {
            "success": True,
            "modes": modes
        }
        
    except Exception as e:
        logger.error(f"Failed to get agent modes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v1/agent/models")
async def get_available_models():
    """获取可用的模型列表"""
    try:
        models = {
            "qwen2.5:7b": {
                "id": "qwen2.5:7b",
                "name": "Qwen2.5 7B",
                "description": "通义千问2.5 7B模型，平衡性能和速度",
                "size": "7B",
                "provider": "Alibaba",
                "recommended_for": ["日常对话", "简单任务"],
                "performance": {
                    "speed": "快",
                    "quality": "良好",
                    "memory": "低"
                }
            },
            "qwen2.5:14b": {
                "id": "qwen2.5:14b", 
                "name": "Qwen2.5 14B",
                "description": "通义千问2.5 14B模型，更强的推理能力",
                "size": "14B",
                "provider": "Alibaba",
                "recommended_for": ["复杂推理", "专业任务"],
                "performance": {
                    "speed": "中等",
                    "quality": "优秀",
                    "memory": "中等"
                }
            },
            "llama3.1:8b": {
                "id": "llama3.1:8b",
                "name": "Llama 3.1 8B",
                "description": "Meta Llama 3.1 8B模型，开源领先模型",
                "size": "8B", 
                "provider": "Meta",
                "recommended_for": ["代码生成", "逻辑推理"],
                "performance": {
                    "speed": "快",
                    "quality": "优秀",
                    "memory": "低"
                }
            },
            "mistral:7b": {
                "id": "mistral:7b",
                "name": "Mistral 7B",
                "description": "Mistral 7B模型，欧洲开源模型",
                "size": "7B",
                "provider": "Mistral AI",
                "recommended_for": ["多语言", "创意写作"],
                "performance": {
                    "speed": "快",
                    "quality": "良好", 
                    "memory": "低"
                }
            }
        }
        
        return {
            "success": True,
            "models": models
        }
        
    except Exception as e:
        logger.error(f"Failed to get available models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v1/agent/current-config")
async def get_current_config():
    """获取当前Agent配置"""
    try:
        # 这里应该从实际的Agent管理器获取当前配置
        # 暂时返回默认配置
        current_config = {
            "chain": {
                "mode": "chain",
                "model": "qwen2.5:7b",
                "status": "active"
            },
            "agent": {
                "mode": "agent", 
                "model": "qwen2.5:7b",
                "status": "active"
            },
            "langgraph": {
                "mode": "langgraph",
                "model": "qwen2.5:7b", 
                "status": "active"
            }
        }
        
        return {
            "success": True,
            "current_config": current_config
        }
        
    except Exception as e:
        logger.error(f"Failed to get current config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v1/agent/configure")
async def configure_agent(request: Dict[str, Any]):
    """配置Agent模式和模型"""
    try:
        mode = request.get("mode")
        model = request.get("model")
        
        if not mode or not model:
            raise HTTPException(status_code=400, detail="Missing mode or model parameter")
        
        # 验证模式
        valid_modes = ["chain", "agent", "langgraph"]
        if mode not in valid_modes:
            raise HTTPException(status_code=400, detail=f"Invalid mode: {mode}")
        
        # 验证模型
        valid_models = ["qwen2.5:7b", "qwen2.5:14b", "llama3.1:8b", "mistral:7b"]
        if model not in valid_models:
            raise HTTPException(status_code=400, detail=f"Invalid model: {model}")
        
        # 调用现有的模型切换API
        api = AgentAPI()
        await api.initialize()
        
        success = await api.switch_agent_model(mode, model)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully configured {mode} agent with {model} model",
                "config": {
                    "mode": mode,
                    "model": model
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to configure agent")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v1/agent/recommendations")
async def get_model_recommendations():
    """获取模型推荐"""
    try:
        recommendations = {
            "by_task": {
                "daily_chat": {
                    "recommended_model": "qwen2.5:7b",
                    "recommended_mode": "chain",
                    "reason": "快速响应，适合日常对话"
                },
                "complex_analysis": {
                    "recommended_model": "qwen2.5:14b",
                    "recommended_mode": "agent",
                    "reason": "强大推理能力，支持复杂工具调用"
                },
                "workflow_automation": {
                    "recommended_model": "llama3.1:8b",
                    "recommended_mode": "langgraph", 
                    "reason": "优秀的逻辑推理，适合复杂工作流"
                },
                "creative_writing": {
                    "recommended_model": "mistral:7b",
                    "recommended_mode": "chain",
                    "reason": "创意能力强，多语言支持好"
                }
            },
            "by_performance": {
                "fastest": {
                    "model": "qwen2.5:7b",
                    "mode": "chain"
                },
                "most_capable": {
                    "model": "qwen2.5:14b", 
                    "mode": "langgraph"
                },
                "balanced": {
                    "model": "llama3.1:8b",
                    "mode": "agent"
                }
            }
        }
        
        return {
            "success": True,
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
