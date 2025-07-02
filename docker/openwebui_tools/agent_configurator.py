"""
Agent配置工具
在OpenWebUI中提供Agent模式和模型配置功能
"""

import json
import requests
from typing import Dict, Any, List


def agent_configurator(
    action: str = "list_modes",
    mode: str = None,
    model: str = None
) -> str:
    """
    Agent配置工具
    
    Args:
        action: 操作类型 (list_modes, list_models, configure, get_current, test_chat)
        mode: Agent模式 (chain, agent, langgraph)
        model: 模型名称 (如 qwen2.5:7b)
    
    Returns:
        配置结果或信息
    """
    
    base_url = "http://langchain-backend:8000"
    
    try:
        if action == "list_modes":
            # 列出可用的Agent模式
            response = requests.get(f"{base_url}/v1/agent/modes", timeout=10)
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
        
        elif action == "list_models":
            # 列出可用的模型
            response = requests.get(f"{base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                
                result = "🧠 可用的模型:\n\n"
                for model in models:
                    name = model.get("name", "")
                    size = model.get("size", 0)
                    size_gb = f"{size / 1000000000:.1f}GB" if size > 0 else "未知大小"
                    result += f"• **{name}** ({size_gb})\n"
                
                return result
            else:
                return f"❌ 获取模型列表失败: {response.status_code}"
        
        elif action == "configure":
            # 配置Agent模式和模型
            if not mode or not model:
                return "❌ 请提供mode和model参数"
            
            payload = {
                "mode": mode,
                "model": model
            }
            
            response = requests.post(
                f"{base_url}/v1/agent/configure",
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
        
        elif action == "get_current":
            # 获取当前配置
            response = requests.get(f"{base_url}/v1/agent/current-config", timeout=10)
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
                return f"❌ 获取当前配置失败: {response.status_code}"
        
        elif action == "test_chat":
            # 测试对话
            if not mode:
                return "❌ 请提供mode参数"
            
            model_id = f"langchain-{mode}-mode"
            payload = {
                "model": model_id,
                "messages": [
                    {
                        "role": "user",
                        "content": "你好，请介绍一下你当前的配置和能力"
                    }
                ],
                "stream": False,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{base_url}/v1/chat/completions",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return f"💬 {mode} Agent 测试成功!\n\n回复: {content[:200]}..."
            else:
                return f"❌ 测试对话失败: {response.status_code}"
        
        elif action == "recommendations":
            # 获取推荐配置
            response = requests.get(f"{base_url}/v1/agent/recommendations", timeout=10)
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
                
                # 性能推荐
                by_performance = recommendations.get("by_performance", {})
                result += "**按性能特点推荐:**\n"
                for perf, rec in by_performance.items():
                    mode = rec.get("mode", "")
                    model = rec.get("model", "")
                    result += f"• {perf}: {mode} + {model}\n"
                
                return result
            else:
                return f"❌ 获取推荐失败: {response.status_code}"
        
        else:
            return f"❌ 未知操作: {action}\n\n可用操作: list_modes, list_models, configure, get_current, test_chat, recommendations"
    
    except Exception as e:
        return f"❌ 操作失败: {str(e)}"


# OpenWebUI工具定义
def get_tools():
    """返回OpenWebUI格式的工具定义"""
    return [
        {
            "name": "agent_configurator",
            "description": "配置和管理LangChain Agent模式和模型",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "操作类型",
                        "enum": ["list_modes", "list_models", "configure", "get_current", "test_chat", "recommendations"]
                    },
                    "mode": {
                        "type": "string",
                        "description": "Agent模式 (chain, agent, langgraph)",
                        "enum": ["chain", "agent", "langgraph"]
                    },
                    "model": {
                        "type": "string",
                        "description": "模型名称 (如 qwen2.5:7b)"
                    }
                },
                "required": ["action"]
            },
            "function": agent_configurator
        }
    ]


if __name__ == "__main__":
    # 测试工具
    print("测试Agent配置工具...")
    
    # 测试列出模式
    result = agent_configurator("list_modes")
    print("列出模式:")
    print(result)
    print("-" * 50)
    
    # 测试列出模型
    result = agent_configurator("list_models")
    print("列出模型:")
    print(result)
    print("-" * 50)
    
    # 测试获取当前配置
    result = agent_configurator("get_current")
    print("当前配置:")
    print(result)
