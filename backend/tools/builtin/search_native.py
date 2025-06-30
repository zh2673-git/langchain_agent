"""
使用 LangChain 原生 @tool 装饰器的搜索工具
"""
import asyncio
import aiohttp
from typing import Dict, Any
from langchain_core.tools import tool

from ...utils.logger import get_logger

logger = get_logger(__name__)


@tool
async def web_search(query: str, max_results: int = 5) -> str:
    """在网络上搜索信息
    
    Args:
        query: 搜索查询词
        max_results: 最大返回结果数，默认5个
    
    Returns:
        搜索结果的文本描述
    """
    try:
        # 这里使用模拟搜索，实际项目中可以接入真实的搜索API
        base_results = [
            f"关于 '{query}' 的相关信息...",
            f"{query} 的详细说明和用途...",
            f"如何使用 {query} 的最佳实践...",
            f"{query} 的常见问题解答...",
            f"{query} 的最新发展动态..."
        ]

        # 格式化结果并限制数量
        results = [f"搜索结果 {i+1}: {result}" for i, result in enumerate(base_results)]
        limited_results = results[:max_results]
        return f"搜索 '{query}' 的结果:\n\n" + "\n\n".join(limited_results)
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"搜索失败: {str(e)}"


@tool
def local_search(query: str, search_type: str = "general") -> str:
    """在本地知识库中搜索信息
    
    Args:
        query: 搜索查询词
        search_type: 搜索类型，可选值：general（通用）, technical（技术）, docs（文档）
    
    Returns:
        本地搜索结果
    """
    try:
        # 模拟本地搜索
        if search_type == "technical":
            return f"技术搜索结果: 关于 '{query}' 的技术文档和API参考..."
        elif search_type == "docs":
            return f"文档搜索结果: '{query}' 相关的使用文档和教程..."
        else:
            return f"通用搜索结果: '{query}' 的基本信息和概述..."
            
    except Exception as e:
        logger.error(f"Local search failed: {e}")
        return f"本地搜索失败: {str(e)}"


# 兼容性包装类
from ...base.tool_base import ToolBase, ToolSchema, ToolParameter, ToolResult, ToolType

class NativeSearchTool(ToolBase):
    """使用原生 @tool 装饰器的搜索工具包装类"""
    
    def __init__(self):
        super().__init__(
            name="search",
            description="在网络或本地搜索信息",
            tool_type=ToolType.SEARCH
        )
        self.web_search_tool = web_search
        self.local_search_tool = local_search
    
    async def initialize(self) -> bool:
        """初始化工具"""
        self._initialized = True
        logger.info("NativeSearchTool initialized successfully")
        return True
    
    def get_schema(self) -> ToolSchema:
        """获取工具模式"""
        if not self._schema:
            self._schema = ToolSchema(
                name=self.name,
                description=self.description,
                tool_type=self.tool_type,
                parameters=[
                    ToolParameter(
                        name="query",
                        type="string",
                        description="搜索查询词",
                        required=True
                    ),
                    ToolParameter(
                        name="search_type",
                        type="string",
                        description="搜索类型",
                        required=False,
                        default="web",
                        enum=["web", "local"]
                    ),
                    ToolParameter(
                        name="max_results",
                        type="number",
                        description="最大返回结果数",
                        required=False,
                        default=5
                    )
                ]
            )
        return self._schema
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行搜索"""
        try:
            self.validate_parameters(kwargs)
            
            query = kwargs["query"]
            search_type = kwargs.get("search_type", "web")
            max_results = kwargs.get("max_results", 5)
            
            if search_type == "web":
                result = await self.web_search_tool.ainvoke({
                    "query": query,
                    "max_results": max_results
                })
            else:
                result = self.local_search_tool.invoke({
                    "query": query,
                    "search_type": "general"
                })
            
            return ToolResult(
                success=True,
                result=result,
                metadata={
                    "query": query,
                    "search_type": search_type,
                    "max_results": max_results,
                    "tool_type": "native_langchain"
                }
            )
            
        except Exception as e:
            logger.error(f"Native search execution failed: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    def get_web_search_tool(self):
        """获取网络搜索工具"""
        return self.web_search_tool
    
    def get_local_search_tool(self):
        """获取本地搜索工具"""
        return self.local_search_tool
