"""
MCP (Model Context Protocol) 工具模块
支持LangChain 2025的MCP工具集成

MCP是一个开放标准，允许AI应用程序与各种数据源和工具进行安全连接。
LangChain 2025已经原生支持MCP工具。

支持的MCP服务器：
- 文件系统服务器
- 数据库服务器  
- API服务器
- 自定义MCP服务器

使用方式：
1. 配置MCP服务器连接
2. 自动发现和加载MCP工具
3. 与其他工具类型统一管理
"""

__all__ = []
