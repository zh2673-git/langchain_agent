"""
工具模块 - 基于LangChain 2025标准的统一工具管理

目录结构：
- builtin/: 内置示例工具
- community/: LangChain社区工具（动态加载）
- custom/: 用户自定义工具
- mcp/: MCP (Model Context Protocol) 工具

工具类型：
1. 内置工具：项目自带的示例工具
2. 社区工具：LangChain社区提供的工具
3. 自定义工具：用户在custom/目录下添加的工具
4. MCP工具：基于Model Context Protocol的工具
"""
from .builtin import get_example_tools, get_basic_tools, get_advanced_tools
# ToolManager已合并到ToolService中
from .tool_service import ToolService, get_tool_service, initialize_tool_service
from .tool_loader import UnifiedToolLoader, get_tool_loader

__all__ = [
    # 内置工具
    "get_example_tools", "get_basic_tools", "get_advanced_tools",

    # 工具管理
    "ToolService", "get_tool_service", "initialize_tool_service",

    # 工具加载器
    "UnifiedToolLoader", "get_tool_loader"
]
