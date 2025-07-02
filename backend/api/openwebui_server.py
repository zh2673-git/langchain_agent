"""
OpenWebUI兼容的API服务器
提供OpenAI兼容的API接口，可以直接与OpenWebUI集成

特点：
1. 完全兼容OpenAI API格式
2. 支持流式响应
3. 支持多种Agent切换
4. 不修改后端代码
5. 可直接与OpenWebUI集成
"""

import asyncio
import sys
import os
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging

# 初始化logger
logger = logging.getLogger(__name__)

# 导入后端API
from backend.api import AgentAPI
from backend.api.openwebui_config import router as config_router
from backend.api.agent_mode_api import router as agent_mode_router
from backend.api.openwebui_models import router as models_router
from backend.api.openwebui_model_provider import router as model_provider_router


# OpenAI兼容的数据模型
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    stream: bool = False
    temperature: float = 0.7
    max_tokens: Optional[int] = None


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]


class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "langchain-agent"


class OpenWebUIServer:
    """OpenWebUI兼容服务器"""
    
    def __init__(self):
        self.api = AgentAPI()
        self.initialized = False
        self.sessions: Dict[str, str] = {}  # request_id -> session_id
        
        # 支持的模型列表 - 扩展支持工具信息和底层模型配置
        self.models = {
            "langchain-chain": {
                "description": "Chain Agent - 基于Runnable接口组合",
                "agent_type": "chain",
                "supports_tools": True,
                "available_models": ["qwen2.5:7b", "qwen2.5:14b", "llama3.1:8b", "mistral:7b"],
                "default_model": "qwen2.5:7b"
            },
            "langchain-agent": {
                "description": "Agent Agent - 使用create_tool_calling_agent",
                "agent_type": "agent",
                "supports_tools": True,
                "available_models": ["qwen2.5:7b", "qwen2.5:14b", "llama3.1:8b", "mistral:7b"],
                "default_model": "qwen2.5:7b"
            },
            "langchain-langgraph": {
                "description": "LangGraph Agent - 使用状态图实现",
                "agent_type": "langgraph",
                "supports_tools": True,
                "available_models": ["qwen2.5:7b", "qwen2.5:14b", "llama3.1:8b", "mistral:7b"],
                "default_model": "qwen2.5:7b"
            }
        }
    
    async def initialize(self):
        """初始化API"""
        if not self.initialized:
            success = await self.api.initialize()
            if success:
                self.initialized = True
                print("✅ OpenWebUI服务器初始化成功")
            else:
                print("❌ OpenWebUI服务器初始化失败")
                raise Exception("Failed to initialize API")
    
    def get_agent_type_from_model(self, model: str) -> str:
        """从模型名称获取Agent类型"""
        model_mapping = {
            "langchain-chain": "chain",
            "langchain-agent": "agent", 
            "langchain-langgraph": "langgraph"
        }
        return model_mapping.get(model, "chain")
    
    def get_session_id(self, request_id: str) -> str:
        """获取或创建会话ID"""
        if request_id not in self.sessions:
            self.sessions[request_id] = f"openwebui_{uuid.uuid4().hex[:8]}"
        return self.sessions[request_id]
    
    async def chat_completion(self, request: ChatCompletionRequest, request_id: str = None) -> Dict[str, Any]:
        """处理聊天完成请求"""
        if not self.initialized:
            await self.initialize()
        
        # 切换到对应的Agent
        agent_type = self.get_agent_type_from_model(request.model)
        self.api.set_current_agent(agent_type)
        
        # 获取会话ID
        session_id = self.get_session_id(request_id or str(uuid.uuid4()))
        
        # 获取最后一条用户消息
        user_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                user_message = msg.content
                break
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        # 调用后端API
        response = await self.api.chat(
            message=user_message,
            session_id=session_id
        )

        # 确保response是字典格式
        if isinstance(response, str):
            # 如果返回的是字符串，包装成字典格式
            response = {
                "success": True,
                "content": response,
                "tool_calls": []
            }
        elif not isinstance(response, dict):
            # 如果不是字典也不是字符串，转换为字符串
            response = {
                "success": True,
                "content": str(response),
                "tool_calls": []
            }

        if not response.get("success"):
            raise HTTPException(status_code=500, detail=response.get("error", "Unknown error"))

        # 构建OpenAI兼容响应
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
        content = response.get("content", "")
        
        # 添加工具调用信息
        tool_calls = response.get("tool_calls", [])
        if tool_calls:
            tool_info = "\n\n🔧 工具调用:\n"
            for call in tool_calls:
                tool_info += f"- {call.get('tool', 'Unknown')}: {call.get('result', 'No result')}\n"
            content += tool_info
        
        return {
            "id": completion_id,
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": len(user_message.split()),
                "completion_tokens": len(content.split()),
                "total_tokens": len(user_message.split()) + len(content.split())
            }
        }
    
    async def chat_completion_stream(self, request: ChatCompletionRequest, request_id: str = None) -> AsyncGenerator[str, None]:
        """处理流式聊天完成请求"""
        if not self.initialized:
            await self.initialize()
        
        # 切换到对应的Agent
        agent_type = self.get_agent_type_from_model(request.model)
        self.api.set_current_agent(agent_type)
        
        # 获取会话ID
        session_id = self.get_session_id(request_id or str(uuid.uuid4()))
        
        # 获取最后一条用户消息
        user_message = None
        for msg in reversed(request.messages):
            if msg.role == "user":
                user_message = msg.content
                break
        
        if not user_message:
            raise HTTPException(status_code=400, detail="No user message found")
        
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
        
        try:
            # 使用流式API
            async for chunk in self.api.chat_stream(
                message=user_message,
                session_id=session_id
            ):
                # 确保chunk是字典格式
                if isinstance(chunk, str):
                    chunk = {
                        "success": True,
                        "content": chunk,
                        "done": False
                    }
                elif not isinstance(chunk, dict):
                    chunk = {
                        "success": True,
                        "content": str(chunk),
                        "done": False
                    }

                if chunk.get("success"):
                    content = chunk.get("content", "")
                    if content:
                        # 构建流式响应块
                        chunk_data = {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": int(datetime.now().timestamp()),
                            "model": request.model,
                            "choices": [{
                                "index": 0,
                                "delta": {
                                    "content": content
                                },
                                "finish_reason": None
                            }]
                        }
                        yield f"data: {json.dumps(chunk_data)}\n\n"
                    
                    # 检查是否完成
                    if chunk.get("done"):
                        # 发送结束标记
                        final_chunk = {
                            "id": completion_id,
                            "object": "chat.completion.chunk",
                            "created": int(datetime.now().timestamp()),
                            "model": request.model,
                            "choices": [{
                                "index": 0,
                                "delta": {},
                                "finish_reason": "stop"
                            }]
                        }
                        yield f"data: {json.dumps(final_chunk)}\n\n"
                        yield "data: [DONE]\n\n"
                        break
        
        except Exception as e:
            # 错误处理
            error_chunk = {
                "id": completion_id,
                "object": "chat.completion.chunk",
                "created": int(datetime.now().timestamp()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {
                        "content": f"❌ 错误: {str(e)}"
                    },
                    "finish_reason": "stop"
                }]
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            yield "data: [DONE]\n\n"


# 创建FastAPI应用
app = FastAPI(
    title="LangChain Agent OpenWebUI API",
    description="OpenWebUI兼容的LangChain Agent API服务器",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建服务器实例
server = OpenWebUIServer()

# 添加配置路由
app.include_router(config_router)
app.include_router(agent_mode_router)
# app.include_router(models_router)  # 移除冲突的路由
app.include_router(model_provider_router)


# Ollama代理API
@app.get("/api/tags")
async def proxy_ollama_tags():
    """代理Ollama的模型列表API"""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://host.docker.internal:11434/api/tags", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                # 返回默认模型列表
                return {
                    "models": [
                        {"name": "qwen2.5:7b", "size": 4000000000},
                        {"name": "qwen2.5:14b", "size": 8000000000},
                        {"name": "llama3.1:8b", "size": 5000000000},
                        {"name": "mistral:7b", "size": 4000000000}
                    ]
                }
    except Exception as e:
        logger.error(f"Failed to proxy Ollama tags: {e}")
        return {
            "models": [
                {"name": "qwen2.5:7b", "size": 4000000000},
                {"name": "qwen2.5:14b", "size": 8000000000},
                {"name": "llama3.1:8b", "size": 5000000000},
                {"name": "mistral:7b", "size": 4000000000}
            ]
        }


@app.on_event("startup")
async def startup_event():
    """启动事件"""
    await server.initialize()


@app.get("/v1/models")
async def list_models():
    """列出可用模型 - Agent模式和模型分离的组合模型"""
    try:
        # 使用新的模型提供者
        from backend.api.openwebui_model_provider import get_openwebui_models
        result = await get_openwebui_models()
        logger.info(f"Model provider returned {len(result.get('data', []))} models")
        return result
    except Exception as e:
        logger.error(f"Failed to get models from provider: {e}")
        logger.exception("Full exception details:")
        # 降级到旧的模型列表
        models = []

        # 获取工具信息
        tools_info = []
        if server.api and hasattr(server.api, 'tool_service') and server.api.tool_service:
            try:
                tool_names = server.api.tool_service.list_tool_names()
                for tool_name in tool_names:
                    tool_info = server.api.tool_service.get_tool_info(tool_name)
                    if tool_info:
                        tools_info.append({
                            "name": tool_name,
                            "description": tool_info.get("description", ""),
                            "parameters": tool_info.get("parameters", {})
                        })
            except Exception as e:
                print(f"获取工具信息失败: {e}")

        for model_id, model_config in server.models.items():
            model_data = {
                "id": model_id,
                "object": "model",
                "created": int(datetime.now().timestamp()),
                "owned_by": "langchain-agent",
                "description": model_config["description"],
                "agent_type": model_config["agent_type"],
                "supports_tools": model_config["supports_tools"],
                "available_models": model_config["available_models"],
                "default_model": model_config["default_model"]
            }

            # 如果支持工具，添加工具信息
            if model_config["supports_tools"] and tools_info:
                model_data["tools"] = tools_info

            models.append(model_data)

        return {"object": "list", "data": models}


@app.post("/v1/models/{agent_type}/switch")
async def switch_model(agent_type: str, request: dict):
    """为指定Agent切换底层模型"""
    try:
        new_model = request.get("model")
        if not new_model:
            raise HTTPException(status_code=400, detail="Missing model parameter")

        # 验证agent_type
        agent_model_id = f"langchain-{agent_type}"
        if agent_model_id not in server.models:
            raise HTTPException(status_code=404, detail=f"Agent type {agent_type} not found")

        # 验证模型是否在可用列表中
        available_models = server.models[agent_model_id]["available_models"]
        if new_model not in available_models:
            raise HTTPException(
                status_code=400,
                detail=f"Model {new_model} not available for {agent_type}. Available: {available_models}"
            )

        # 调用后端API切换模型
        success = await server.api.switch_agent_model(agent_type, new_model)

        if success:
            return {
                "success": True,
                "message": f"Successfully switched {agent_type} to model {new_model}",
                "agent_type": agent_type,
                "new_model": new_model
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to switch model")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/tools")
async def list_tools():
    """列出所有可用工具"""
    try:
        if not server.api or not hasattr(server.api, 'tool_service') or not server.api.tool_service:
            return {"tools": [], "message": "Tool service not available"}

        tool_names = server.api.tool_service.list_tool_names()
        tools = []

        for tool_name in tool_names:
            tool_info = server.api.tool_service.get_tool_info(tool_name)
            if tool_info:
                tools.append({
                    "name": tool_name,
                    "description": tool_info.get("description", ""),
                    "parameters": tool_info.get("parameters", {}),
                    "enabled": True
                })

        return {
            "tools": tools,
            "count": len(tools),
            "message": f"Found {len(tools)} available tools"
        }

    except Exception as e:
        return {
            "tools": [],
            "error": str(e),
            "message": "Failed to retrieve tools"
        }


@app.post("/v1/tools/execute")
async def execute_tool(request: dict):
    """执行工具（供OpenWebUI工具调用）"""
    try:
        tool_name = request.get("tool_name")
        parameters = request.get("parameters", {})

        if not tool_name:
            raise HTTPException(status_code=400, detail="Missing tool_name parameter")

        if not server.api or not hasattr(server.api, 'tool_service') or not server.api.tool_service:
            raise HTTPException(status_code=500, detail="Tool service not available")

        # 执行工具
        result = await server.api.tool_service.execute_tool(tool_name, **parameters)

        return {
            "success": True,
            "tool_name": tool_name,
            "result": result.get("result", ""),
            "message": "Tool executed successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")


@app.get("/v1/tools/openwebui")
async def get_openwebui_tools():
    """获取OpenWebUI格式的工具"""
    try:
        if not server.api or not hasattr(server.api, 'tool_service') or not server.api.tool_service:
            return {"tools": {}, "message": "Tool service not available"}

        # 获取OpenWebUI格式的工具
        openwebui_tools = server.api.tool_service.get_openwebui_tools()

        return {
            "tools": openwebui_tools,
            "count": len(openwebui_tools),
            "message": f"Found {len(openwebui_tools)} OpenWebUI tools"
        }

    except Exception as e:
        return {
            "tools": {},
            "error": str(e),
            "message": "Failed to retrieve OpenWebUI tools"
        }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, http_request: Request):
    """聊天完成API"""
    request_id = http_request.headers.get("x-request-id", str(uuid.uuid4()))

    # 临时修复：强制所有请求使用非流式响应以兼容OpenWebUI
    # OpenWebUI发送流式请求但期望JSON响应，这是一个兼容性问题

    # 强制设置为非流式
    request.stream = False

    # 非流式响应
    response = await server.chat_completion(request, request_id)
    return JSONResponse(
        content=response,
        headers={
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    )


@app.get("/")
async def root():
    """根路径处理"""
    return {
        "message": "LangChain Agent OpenWebUI API Server",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "models": "/v1/models",
        "chat": "/v1/chat/completions"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "initialized": server.initialized,
        "models": list(server.models.keys()),
        "timestamp": datetime.now().isoformat()
    }


def main():
    """主函数"""
    print("🚀 启动OpenWebUI兼容服务器...")
    print("📱 API地址: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    print("🔧 支持的模型:")
    for model_id, description in server.models.items():
        print(f"   - {model_id}: {description}")
    print("\n💡 OpenWebUI配置:")
    print("   1. 在OpenWebUI中添加自定义模型")
    print("   2. API Base URL: http://localhost:8000/v1")
    print("   3. API Key: 任意值（不验证）")
    print("   4. 模型名称: langchain-chain, langchain-agent, langchain-langgraph")
    
    uvicorn.run(
        "openwebui_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
