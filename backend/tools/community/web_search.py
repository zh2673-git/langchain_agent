"""
社区工具：网络搜索
基于DuckDuckGo的免费网络搜索工具
"""

from typing import Optional
from langchain_core.tools import BaseTool
from backend.tools.adapters.universal_tool_adapter import universal_adapter
import logging

logger = logging.getLogger(__name__)


def create_duckduckgo_tool() -> Optional[BaseTool]:
    """创建DuckDuckGo搜索工具"""
    try:
        from langchain_community.tools import DuckDuckGoSearchRun
        
        search = DuckDuckGoSearchRun()
        return search
    except ImportError:
        logger.warning("DuckDuckGo tool requires: pip install duckduckgo-search")
        return None


def web_search(query: str, num_results: int = 5) -> str:
    """
    搜索网络信息
    
    Args:
        query: 搜索查询
        num_results: 返回结果数量
    
    Returns:
        搜索结果
    """
    try:
        tool = create_duckduckgo_tool()
        if tool:
            return tool.run(query)
        else:
            # 降级到简单的API搜索
            return _fallback_search(query, num_results)
    except Exception as e:
        return f"网络搜索失败: {str(e)}"


def _fallback_search(query: str, num_results: int = 5) -> str:
    """降级搜索方案"""
    try:
        import requests
        from urllib.parse import quote
        
        # 使用DuckDuckGo即时搜索API
        url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json&no_html=1&skip_disambig=1"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        # 主要答案
        if data.get('Answer'):
            results.append(f"答案: {data['Answer']}")
        
        # 摘要
        if data.get('Abstract'):
            results.append(f"摘要: {data['Abstract']}")
        
        # 相关主题
        if data.get('RelatedTopics'):
            for i, topic in enumerate(data['RelatedTopics'][:num_results]):
                if isinstance(topic, dict) and 'Text' in topic:
                    results.append(f"相关 {i+1}: {topic['Text']}")
        
        return "\n".join(results[:num_results]) if results else "未找到相关信息"
        
    except Exception as e:
        return f"搜索失败: {str(e)}"


# 注册到统一适配器
def register_web_search_tool():
    """注册网络搜索工具到统一适配器"""
    try:
        universal_adapter.register_tool(
            name="web_search",
            function=web_search,
            description="搜索网络信息，获取实时数据和答案",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询，例如 '今天天气' 或 '最新新闻'"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "返回结果数量，默认5个",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["query"]
            }
        )
    except Exception as e:
        logger.error(f"Failed to register web search tool: {e}")


# 自动注册
register_web_search_tool()

# 导出工具
web_search_tool = create_duckduckgo_tool()
__all__ = ["web_search_tool", "web_search"]
