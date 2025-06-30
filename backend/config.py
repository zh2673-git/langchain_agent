"""
项目配置管理模块
统一管理模型、会话、工具等参数配置
"""
import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """项目配置类"""
    
    # 模型供应商配置
    MODEL_PROVIDER: str = os.getenv("MODEL_PROVIDER", "ollama")  # ollama, openai, anthropic
    DEFAULT_MODEL_PROVIDER: str = os.getenv("DEFAULT_MODEL_PROVIDER", "ollama")
    DEFAULT_MODEL_NAME: str = os.getenv("DEFAULT_MODEL_NAME", "qwen2.5:7b")
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))

    # Ollama 配置
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

    # OpenAI 配置 (可选)
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    # Anthropic 配置 (可选)
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
    
    # 搜索 API 配置
    SERPAPI_API_KEY: Optional[str] = os.getenv("SERPAPI_API_KEY")
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    GOOGLE_CSE_ID: Optional[str] = os.getenv("GOOGLE_CSE_ID")
    
    # 向量数据库配置
    CHROMA_PERSIST_DIRECTORY: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "./logs/app.log")
    
    # MCP 配置
    MCP_SERVER_PORT: int = int(os.getenv("MCP_SERVER_PORT", "8080"))
    MCP_SERVER_HOST: str = os.getenv("MCP_SERVER_HOST", "localhost")
    
    # Agent 配置
    AGENT_CONFIG: Dict[str, Any] = {
        "max_iterations": 10,
        "max_execution_time": 300,  # 5分钟
        "temperature": 0.7,
        "max_tokens": 2048,
        "verbose": True
    }
    
    # 记忆配置
    MEMORY_CONFIG: Dict[str, Any] = {
        "max_token_limit": 4000,
        "return_messages": True,
        "memory_key": "chat_history",
        "input_key": "input",
        "output_key": "output"
    }
    
    # 工具配置
    TOOLS_CONFIG: Dict[str, Any] = {
        "search": {
            "enabled": True,
            "max_results": 5,
            "timeout": 10
        },
        "calculator": {
            "enabled": True,
            "precision": 10
        },
        "custom_tools": {
            "enabled": True,
            "auto_load": True
        }
    }

    # 支持的模型配置
    SUPPORTED_MODELS: Dict[str, Dict[str, Any]] = {
        "ollama": {
            "name": "Ollama",
            "models": [
                "glm4:latest",
                "qwen3:8b",
                "qwen3:4b",
                "qwen3:14b",
                "qwen3:32b-q4_K_M",
                "mistral:7b",
                "gemma3:4b",
                "gemma3:12b",
                "deepseek-r1:1.5b",
                "deepseek-r1:7b",
                "deepseek-r1:8b",
                "deepseek-r1:14b"
            ],
            "supports_tools": {
                "glm4:latest": False,
                "qwen3:8b": True,
                "qwen3:4b": True,
                "qwen3:14b": True,
                "qwen3:32b-q4_K_M": True,
                "mistral:7b": True,
                "gemma3:4b": True,
                "gemma3:12b": True,
                "deepseek-r1:1.5b": False,
                "deepseek-r1:7b": True,
                "deepseek-r1:8b": True,
                "deepseek-r1:14b": True
            }
        },
        "openai": {
            "name": "OpenAI",
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

    @classmethod
    def get_model_config(cls) -> Dict[str, Any]:
        """获取模型配置"""
        provider = cls.MODEL_PROVIDER
        if provider == "ollama":
            return {
                "provider": "ollama",
                "model": cls.OLLAMA_MODEL,
                "base_url": cls.OLLAMA_BASE_URL,
                "temperature": cls.AGENT_CONFIG.get("temperature", 0.7),
                "max_tokens": cls.AGENT_CONFIG.get("max_tokens", 2048)
            }
        elif provider == "openai":
            return {
                "provider": "openai",
                "model": cls.OPENAI_MODEL,
                "api_key": cls.OPENAI_API_KEY,
                "temperature": cls.AGENT_CONFIG.get("temperature", 0.7),
                "max_tokens": cls.AGENT_CONFIG.get("max_tokens", 2048)
            }
        elif provider == "anthropic":
            return {
                "provider": "anthropic",
                "model": cls.ANTHROPIC_MODEL,
                "api_key": cls.ANTHROPIC_API_KEY,
                "temperature": cls.AGENT_CONFIG.get("temperature", 0.7),
                "max_tokens": cls.AGENT_CONFIG.get("max_tokens", 2048)
            }
        else:
            raise ValueError(f"Unsupported model provider: {provider}")

    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """获取支持的模型供应商列表"""
        return list(cls.SUPPORTED_MODELS.keys())

    @classmethod
    def get_provider_models(cls, provider: str) -> List[str]:
        """获取指定供应商的模型列表"""
        if provider not in cls.SUPPORTED_MODELS:
            return []
        return cls.SUPPORTED_MODELS[provider]["models"]

    @classmethod
    def model_supports_tools(cls, provider: str, model: str) -> bool:
        """检查模型是否支持工具调用"""
        if provider not in cls.SUPPORTED_MODELS:
            return False
        supports_tools = cls.SUPPORTED_MODELS[provider].get("supports_tools", {})
        return supports_tools.get(model, False)

    @classmethod
    def set_model_config(cls, provider: str, model: str):
        """设置模型配置"""
        if provider not in cls.SUPPORTED_MODELS:
            raise ValueError(f"Unsupported provider: {provider}")

        if model not in cls.SUPPORTED_MODELS[provider]["models"]:
            raise ValueError(f"Unsupported model {model} for provider {provider}")

        cls.MODEL_PROVIDER = provider
        if provider == "ollama":
            cls.OLLAMA_MODEL = model
        elif provider == "openai":
            cls.OPENAI_MODEL = model
        elif provider == "anthropic":
            cls.ANTHROPIC_MODEL = model
    
    @classmethod
    def get_memory_config(cls) -> Dict[str, Any]:
        """获取记忆配置"""
        return cls.MEMORY_CONFIG.copy()
    
    @classmethod
    def get_tools_config(cls) -> Dict[str, Any]:
        """获取工具配置"""
        return cls.TOOLS_CONFIG.copy()
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证配置是否有效"""
        # 检查必要的配置项
        if not cls.OLLAMA_BASE_URL:
            raise ValueError("OLLAMA_BASE_URL is required")
        
        if not cls.OLLAMA_MODEL:
            raise ValueError("OLLAMA_MODEL is required")
        
        # 创建必要的目录
        os.makedirs(os.path.dirname(cls.LOG_FILE), exist_ok=True)
        os.makedirs(cls.CHROMA_PERSIST_DIRECTORY, exist_ok=True)
        
        return True


# 全局配置实例
config = Config()

# 验证配置
try:
    config.validate_config()
except Exception as e:
    print(f"配置验证失败: {e}")
    raise
