"""
自动处理验证工具
验证添加新工具后是否能自动被系统识别和处理
"""

from langchain_core.tools import tool
from backend.tools.adapters.universal_tool_adapter import universal_adapter
import logging

logger = logging.getLogger(__name__)


@tool
def verify_auto_processing(message: str) -> str:
    """
    验证自动处理功能
    
    Args:
        message: 验证消息
    
    Returns:
        处理结果
    """
    return f"✅ 自动处理验证成功！收到消息: {message}"


def string_processor(text: str, operation: str = "upper") -> str:
    """
    字符串处理器
    
    Args:
        text: 输入文本
        operation: 操作类型 (upper, lower, reverse, length)
    
    Returns:
        处理结果
    """
    try:
        if operation == "upper":
            return f"大写转换: {text.upper()}"
        elif operation == "lower":
            return f"小写转换: {text.lower()}"
        elif operation == "reverse":
            return f"反转文本: {text[::-1]}"
        elif operation == "length":
            return f"文本长度: {len(text)} 字符"
        else:
            return f"未知操作: {operation}，支持的操作: upper, lower, reverse, length"
    except Exception as e:
        return f"❌ 处理失败: {str(e)}"


# 注册到统一适配器
def register_verification_tools():
    """注册验证工具到统一适配器"""
    try:
        universal_adapter.register_tool(
            name="string_processor",
            function=string_processor,
            description="字符串处理工具，支持大小写转换、反转和长度计算",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "要处理的文本"
                    },
                    "operation": {
                        "type": "string",
                        "description": "操作类型",
                        "enum": ["upper", "lower", "reverse", "length"],
                        "default": "upper"
                    }
                },
                "required": ["text"]
            }
        )
        logger.info("Verification tools registered successfully")
    except Exception as e:
        logger.error(f"Failed to register verification tools: {e}")


# 自动注册
register_verification_tools()

# 导出工具
__all__ = ["verify_auto_processing", "string_processor"]
