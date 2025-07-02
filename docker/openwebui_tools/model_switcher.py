"""
OpenWebUI工具: 模型切换器
在OpenWebUI界面中提供Agent模型切换功能
"""

from typing import Any, Dict, List
import json
import requests


class Tools:
    def __init__(self):
        self.citation = True

    def switch_agent_model(self, agent_type: str, new_model: str) -> str:
        """
        切换Agent的底层模型
        
        :param agent_type: Agent类型 (chain, agent, langgraph)
        :param new_model: 新的模型名称 (qwen2.5:7b, qwen2.5:14b, llama3.1:8b, mistral:7b)
        """
        try:
            # 调用LangChain后端API
            url = f"http://langchain-backend:8000/v1/models/{agent_type}/switch"
            payload = {"model": new_model}
            
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    return f"✅ 成功切换 {agent_type} Agent 到模型 {new_model}"
                else:
                    return f"❌ 切换失败: {result.get('message', '未知错误')}"
            else:
                return f"❌ 切换请求失败: HTTP {response.status_code}"
                
        except Exception as e:
            return f"❌ 切换异常: {str(e)}"

    def get_agent_models_info(self) -> str:
        """
        获取所有Agent的模型信息
        """
        try:
            # 调用配置API
            url = "http://langchain-backend:8000/v1/models/config"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", {})
                
                result = "🤖 Agent模型信息:\n\n"
                
                for model_id, config in models.items():
                    agent_type = config.get("agent_type", "")
                    current_model = config.get("current_model", "")
                    available_models = config.get("available_models", [])
                    
                    result += f"**{config.get('name', model_id)}**\n"
                    result += f"- 类型: {agent_type}\n"
                    result += f"- 当前模型: {current_model}\n"
                    result += f"- 可用模型: {', '.join([m['id'] for m in available_models])}\n\n"
                
                return result
            else:
                return f"❌ 获取模型信息失败: HTTP {response.status_code}"
                
        except Exception as e:
            return f"❌ 获取信息异常: {str(e)}"

    def list_available_tools(self) -> str:
        """
        列出所有可用的工具
        """
        try:
            # 调用工具配置API
            url = "http://langchain-backend:8000/v1/tools/config"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                tools = data.get("tools", [])
                total = data.get("total", 0)
                
                result = f"🔧 可用工具列表 (共{total}个):\n\n"
                
                # 按类别分组
                categories = {}
                for tool in tools:
                    category = tool.get("category", "其他")
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(tool)
                
                for category, category_tools in categories.items():
                    result += f"**{category}类工具:**\n"
                    for tool in category_tools[:10]:  # 每类最多显示10个
                        name = tool.get("name", "")
                        description = tool.get("description", "")
                        result += f"- `{name}`: {description[:50]}...\n"
                    
                    if len(category_tools) > 10:
                        result += f"- ... 还有 {len(category_tools) - 10} 个工具\n"
                    result += "\n"
                
                return result
            else:
                return f"❌ 获取工具列表失败: HTTP {response.status_code}"
                
        except Exception as e:
            return f"❌ 获取工具异常: {str(e)}"


# OpenWebUI工具规范
class ModelSwitcherTool:
    """
    OpenWebUI模型切换工具
    """
    
    def __init__(self):
        self.tools = Tools()
    
    def get_tools(self):
        return {
            "switch_agent_model": {
                "callable": self.tools.switch_agent_model,
                "description": "切换Agent的底层模型",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "agent_type": {
                            "type": "string",
                            "enum": ["chain", "agent", "langgraph"],
                            "description": "Agent类型"
                        },
                        "new_model": {
                            "type": "string", 
                            "enum": ["qwen2.5:7b", "qwen2.5:14b", "llama3.1:8b", "mistral:7b"],
                            "description": "新的模型名称"
                        }
                    },
                    "required": ["agent_type", "new_model"]
                }
            },
            "get_agent_models_info": {
                "callable": self.tools.get_agent_models_info,
                "description": "获取所有Agent的模型信息",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            "list_available_tools": {
                "callable": self.tools.list_available_tools,
                "description": "列出所有可用的工具",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }


# 导出工具实例
model_switcher_tool = ModelSwitcherTool()
