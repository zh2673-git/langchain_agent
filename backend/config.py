"""
项目配置管理模块
统一管理模型、API密钥、工具等参数配置

重塑后的配置管理：
1. 统一的API密钥管理
2. 简化的模型配置
3. 工具配置管理
4. 三种Agent实现方式的配置
"""
import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """项目配置类 - 重塑版"""

    # ==================== 基础配置 ====================

    # 默认模型配置
    DEFAULT_MODEL_PROVIDER: str = os.getenv("DEFAULT_MODEL_PROVIDER", "ollama")
    DEFAULT_MODEL_NAME: str = os.getenv("DEFAULT_MODEL_NAME", "qwen2.5:7b")
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))

    # ==================== API密钥管理 ====================

    # LLM API密钥
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")

    # 工具相关API密钥
    SERPAPI_API_KEY: Optional[str] = os.getenv("SERPAPI_API_KEY")  # 搜索工具
    GOOGLE_CSE_ID: Optional[str] = os.getenv("GOOGLE_CSE_ID")     # Google搜索
    WEATHER_API_KEY: Optional[str] = os.getenv("WEATHER_API_KEY") # 天气工具
    NEWS_API_KEY: Optional[str] = os.getenv("NEWS_API_KEY")       # 新闻工具

    # 数据库API密钥
    MONGODB_URI: Optional[str] = os.getenv("MONGODB_URI")
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")

    # ==================== 服务配置 ====================

    # Ollama配置
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # 向量数据库配置
    CHROMA_PERSIST_DIRECTORY: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")

    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "./logs/app.log")
    
    # ==================== 三种Agent实现配置 ====================

    # Chain Agent配置
    CHAIN_AGENT_CONFIG: Dict[str, Any] = {
        "temperature": 0.7,
        "max_tokens": 2048,
        "streaming": True,
        "tool_call_method": "prompt"  # 使用提示词方式调用工具
    }

    # Agent Agent配置
    AGENT_AGENT_CONFIG: Dict[str, Any] = {
        "temperature": 0.7,
        "max_tokens": 2048,
        "max_iterations": 5,
        "verbose": True,
        "handle_parsing_errors": True,
        "tool_call_method": "function"  # 使用function calling
    }

    # LangGraph Agent配置
    LANGGRAPH_AGENT_CONFIG: Dict[str, Any] = {
        "temperature": 0.7,
        "max_tokens": 2048,
        "streaming": True,
        "checkpointer": "memory",  # memory 或 sqlite
        "tool_call_method": "function"
    }

    # ==================== 服务配置 ====================

    # 记忆服务配置
    MEMORY_SERVICE_CONFIG: Dict[str, Any] = {
        "default_type": "sqlite",  # memory, sqlite, chroma
        "max_sessions": 1000,
        "max_messages": 100,
        "max_token_limit": 4000,
        "session_timeout": 3600,  # 1小时
        "sqlite_db_path": "./data/chat_history.db",
        "auto_backup": True,
        "backup_interval": 3600  # 1小时备份一次
    }

    # 工具服务配置
    TOOL_SERVICE_CONFIG: Dict[str, Any] = {
        "auto_load_examples": True,
        "enable_custom_tools": True,
        "tool_timeout": 30,  # 工具执行超时时间
        "max_tool_calls": 10  # 单次对话最大工具调用次数
    }

    # ==================== 模型配置 ====================

    # 支持的模型配置（简化版）
    SUPPORTED_MODELS: Dict[str, Dict[str, Any]] = {
        "ollama": {
            "name": "Ollama",
            "base_url": OLLAMA_BASE_URL,
            "models": [
                "qwen2.5:7b",
                "qwen2.5:14b",
                "qwen2.5:32b",
                "llama3.1:8b",
                "llama3.1:70b",
                "mistral:7b",
                "gemma2:9b",
                "deepseek-r1:7b",
                "deepseek-r1:14b"
            ],
            "supports_tools": {
                "qwen2.5:7b": True,
                "qwen2.5:14b": True,
                "qwen2.5:32b": True,
                "llama3.1:8b": True,
                "llama3.1:70b": True,
                "mistral:7b": True,
                "gemma2:9b": True,
                "deepseek-r1:7b": True,
                "deepseek-r1:14b": True
            }
        },
        "openai": {
            "name": "OpenAI",
            "api_key_required": True,
            "models": [
                "gpt-3.5-turbo",
                "gpt-4",
                "gpt-4-turbo",
                "gpt-4o",
                "gpt-4o-mini"
            ],
            "supports_tools": {
                "gpt-3.5-turbo": True,
                "gpt-4": True,
                "gpt-4-turbo": True,
                "gpt-4o": True,
                "gpt-4o-mini": True
            }
        },
        "anthropic": {
            "name": "Anthropic",
            "api_key_required": True,
            "models": [
                "claude-3-sonnet-20240229",
                "claude-3-opus-20240229",
                "claude-3-haiku-20240307",
                "claude-3-5-sonnet-20241022"
            ],
            "supports_tools": {
                "claude-3-sonnet-20240229": True,
                "claude-3-opus-20240229": True,
                "claude-3-haiku-20240307": True,
                "claude-3-5-sonnet-20241022": True
            }
        }
    }

    # ==================== 工具配置 ====================

    # 工具加载配置
    TOOL_LOADING_CONFIG: Dict[str, Any] = {
        "auto_load_builtin": True,
        "auto_load_community": True,
        "auto_load_custom": True,
        "auto_load_mcp": False,  # MCP需要额外配置
        "tool_timeout": 30,
        "max_concurrent_tools": 10
    }

    # 内置工具配置
    BUILTIN_TOOLS_CONFIG: Dict[str, Dict[str, Any]] = {
        # 示例工具
        "simple_calculator": {"enabled": True},
        "weather_query": {"enabled": True},
        "file_operation": {"enabled": True},
        "data_analysis": {"enabled": True},

        # LangChain社区工具
        "wikipedia": {"enabled": True},
        "duckduckgo_search": {"enabled": True},
        "python_repl": {"enabled": False},  # 安全考虑默认关闭
        "shell": {"enabled": False},        # 安全考虑默认关闭
        "requests": {"enabled": True},
        "arxiv": {"enabled": True},
        "wolfram_alpha": {"enabled": False, "api_key_required": True},
        "google_search": {"enabled": False, "api_key_required": True},
        "bing_search": {"enabled": False, "api_key_required": True},
    }

    # 自定义工具配置
    CUSTOM_TOOLS_CONFIG: Dict[str, Any] = {
        "auto_discover": True,
        "file_patterns": ["*.py"],
        "exclude_patterns": ["__*", "test_*"],
        "reload_on_change": True
    }

    # MCP工具配置
    MCP_TOOLS_CONFIG: Dict[str, Any] = {
        "enabled": True,
        "servers": {
            "filesystem": {
                "type": "filesystem",
                "enabled": True,
                "base_path": "./data"
            },
            "example_api": {
                "type": "api",
                "enabled": False,
                "base_url": "https://api.example.com",
                "api_key": ""
            }
        },
        "timeout": 30,
        "retry_attempts": 3
    }

    # ==================== 配置管理方法 ====================

    def model_supports_tools(self, provider: str, model: str) -> bool:
        """检查模型是否支持工具调用"""
        if provider not in self.SUPPORTED_MODELS:
            return False

        provider_config = self.SUPPORTED_MODELS[provider]
        supports_tools = provider_config.get("supports_tools", {})

        return supports_tools.get(model, False)

    def get_model_config(self, provider: str, model: str) -> Dict[str, Any]:
        """获取模型配置"""
        if provider not in self.SUPPORTED_MODELS:
            return {}

        provider_config = self.SUPPORTED_MODELS[provider]

        return {
            "provider": provider,
            "model": model,
            "supports_tools": self.model_supports_tools(provider, model),
            "provider_name": provider_config.get("name", provider),
            "available_models": provider_config.get("models", []),
            "api_key_required": provider_config.get("api_key_required", False)
        }

    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """获取Agent配置"""
        config_map = {
            "chain": self.CHAIN_AGENT_CONFIG,
            "agent": self.AGENT_AGENT_CONFIG,
            "langgraph": self.LANGGRAPH_AGENT_CONFIG
        }

        return config_map.get(agent_type, self.CHAIN_AGENT_CONFIG).copy()

    def get_memory_service_config(self) -> Dict[str, Any]:
        """获取记忆服务配置"""
        return self.MEMORY_SERVICE_CONFIG.copy()

    def get_tool_service_config(self) -> Dict[str, Any]:
        """获取工具服务配置"""
        return self.TOOL_SERVICE_CONFIG.copy()

    def get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """获取特定工具配置"""
        return self.BUILTIN_TOOLS_CONFIG.get(tool_name, {}).copy()

    def is_api_key_configured(self, service: str) -> bool:
        """检查API密钥是否已配置"""
        key_map = {
            "openai": self.OPENAI_API_KEY,
            "anthropic": self.ANTHROPIC_API_KEY,
            "google": self.GOOGLE_API_KEY,
            "serpapi": self.SERPAPI_API_KEY,
            "weather": self.WEATHER_API_KEY,
            "news": self.NEWS_API_KEY
        }

        api_key = key_map.get(service.lower())
        return api_key is not None and api_key.strip() != ""

    def get_api_key(self, service: str) -> Optional[str]:
        """获取指定服务的API密钥"""
        key_map = {
            "openai": self.OPENAI_API_KEY,
            "anthropic": self.ANTHROPIC_API_KEY,
            "google": self.GOOGLE_API_KEY,
            "serpapi": self.SERPAPI_API_KEY,
            "weather": self.WEATHER_API_KEY,
            "news": self.NEWS_API_KEY
        }

        return key_map.get(service.lower())

    def get_available_providers(self) -> List[str]:
        """获取可用的模型供应商"""
        return list(self.SUPPORTED_MODELS.keys())

    def get_available_models(self, provider: str) -> List[str]:
        """获取指定供应商的可用模型"""
        if provider not in self.SUPPORTED_MODELS:
            return []

        return self.SUPPORTED_MODELS[provider].get("models", [])

    def validate_model(self, provider: str, model: str) -> bool:
        """验证模型是否可用"""
        if provider not in self.SUPPORTED_MODELS:
            return False

        available_models = self.get_available_models(provider)
        return model in available_models

    def get_default_model_config(self) -> Dict[str, Any]:
        """获取默认模型配置"""
        return self.get_model_config(self.DEFAULT_MODEL_PROVIDER, self.DEFAULT_MODEL_NAME)

    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要"""
        return {
            "default_model": {
                "provider": self.DEFAULT_MODEL_PROVIDER,
                "model": self.DEFAULT_MODEL_NAME,
                "temperature": self.DEFAULT_TEMPERATURE
            },
            "api_keys_configured": {
                service: self.is_api_key_configured(service)
                for service in ["openai", "anthropic", "google", "serpapi", "weather", "news"]
            },
            "agents_available": ["chain", "agent", "langgraph"],
            "tools_enabled": list(self.BUILTIN_TOOLS_CONFIG.keys()),
            "memory_type": self.MEMORY_SERVICE_CONFIG["default_type"]
        }

    def validate_config(self) -> bool:
        """验证配置是否有效"""
        # 创建必要的目录
        os.makedirs(os.path.dirname(self.LOG_FILE), exist_ok=True)
        os.makedirs(self.CHROMA_PERSIST_DIRECTORY, exist_ok=True)

        return True


# 全局配置实例
config = Config()

# 验证配置
try:
    config.validate_config()
except Exception as e:
    print(f"配置验证失败: {e}")
    raise
