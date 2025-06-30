"""
MCP管理器
管理MCP工具的连接和调用
"""

from typing import Dict, Any, List, Optional
import asyncio
from .mcp_base import MCPToolBase, DemoMCPTool

class MCPManager:
    """MCP工具管理器"""
    
    def __init__(self):
        self.mcp_tools: Dict[str, MCPToolBase] = {}
        self.initialized = False
    
    async def initialize(self) -> bool:
        """初始化MCP管理器"""
        try:
            # 添加演示MCP工具
            demo_tool = DemoMCPTool()
            await demo_tool.initialize()
            self.mcp_tools[demo_tool.name] = demo_tool
            
            self.initialized = True
            return True
        except Exception as e:
            print(f"MCP管理器初始化失败: {e}")
            return False
    
    async def add_mcp_tool(self, tool: MCPToolBase) -> bool:
        """添加MCP工具"""
        try:
            if await tool.initialize():
                self.mcp_tools[tool.name] = tool
                return True
            return False
        except Exception as e:
            print(f"添加MCP工具失败: {e}")
            return False
    
    async def remove_mcp_tool(self, tool_name: str) -> bool:
        """移除MCP工具"""
        try:
            if tool_name in self.mcp_tools:
                tool = self.mcp_tools[tool_name]
                await tool.disconnect_from_mcp_server()
                del self.mcp_tools[tool_name]
                return True
            return False
        except Exception as e:
            print(f"移除MCP工具失败: {e}")
            return False
    
    def list_mcp_tools(self) -> List[Dict[str, Any]]:
        """列出所有MCP工具"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "connected": tool.connected,
                "server_url": getattr(tool, 'mcp_server_url', None)
            }
            for tool in self.mcp_tools.values()
        ]
    
    async def execute_mcp_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """执行MCP工具"""
        try:
            if tool_name not in self.mcp_tools:
                return {
                    "success": False,
                    "error": f"MCP工具 '{tool_name}' 不存在"
                }
            
            tool = self.mcp_tools[tool_name]
            return await tool.execute(**kwargs)
            
        except Exception as e:
            return {
                "success": False,
                "error": f"执行MCP工具失败: {str(e)}"
            }

# 全局MCP管理器实例
mcp_manager = MCPManager()
