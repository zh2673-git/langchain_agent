"""
API模块 - 提供多种API接口

包含：
1. AgentAPI - 核心Agent接口
2. OpenWebUI Server - OpenAI兼容的API服务器
"""

from .api import AgentAPI

__all__ = [
    "AgentAPI"
]

# OpenWebUIServer需要额外依赖，按需导入
try:
    from .openwebui_server import OpenWebUIServer
    __all__.append("OpenWebUIServer")
except ImportError:
    pass
