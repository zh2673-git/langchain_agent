"""
社区工具：Wikipedia搜索
基于LangChain Community的Wikipedia查询工具
"""

from typing import Optional
from langchain_core.tools import BaseTool
from backend.tools.adapters.universal_tool_adapter import universal_adapter
import logging

logger = logging.getLogger(__name__)


def create_wikipedia_tool() -> Optional[BaseTool]:
    """创建Wikipedia搜索工具"""
    try:
        from langchain_community.tools import WikipediaQueryRun
        from langchain_community.utilities import WikipediaAPIWrapper
        
        wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        return wikipedia
    except ImportError:
        logger.warning("Wikipedia tool requires: pip install wikipedia")
        return None


def wikipedia_search(query: str, max_results: int = 3) -> str:
    """
    搜索Wikipedia文章
    
    Args:
        query: 搜索查询
        max_results: 最大结果数量
    
    Returns:
        搜索结果
    """
    try:
        tool = create_wikipedia_tool()
        if tool:
            return tool.run(query)
        else:
            return "Wikipedia工具不可用，请安装依赖: pip install wikipedia"
    except Exception as e:
        return f"Wikipedia搜索失败: {str(e)}"


# 注册到统一适配器
def register_wikipedia_tool():
    """注册Wikipedia工具到统一适配器"""
    try:
        universal_adapter.register_tool(
            name="wikipedia_search",
            function=wikipedia_search,
            description="搜索Wikipedia文章，获取百科知识",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询，例如 '人工智能' 或 'Python编程'"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最大结果数量，默认3个",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["query"]
            }
        )
    except Exception as e:
        logger.error(f"Failed to register wikipedia tool: {e}")


# 自动注册
register_wikipedia_tool()

# 导出工具
wikipedia_tool = create_wikipedia_tool()
__all__ = ["wikipedia_tool", "wikipedia_search"]
