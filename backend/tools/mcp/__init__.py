"""
MCP (Model Context Protocol) 工具支持
为未来的MCP工具集成提供框架
"""

from .mcp_base import MCPToolBase
from .mcp_manager import MCPManager

__all__ = [
    "MCPToolBase",
    "MCPManager"
]
