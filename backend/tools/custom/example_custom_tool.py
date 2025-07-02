"""
自定义工具示例
演示如何创建自定义工具并被自动发现和加载

支持的方式：
1. 使用@tool装饰器
2. 继承BaseTool类
3. 使用StructuredTool.from_function
"""

from typing import Optional
from langchain_core.tools import tool, BaseTool, StructuredTool
try:
    from pydantic import BaseModel, Field
except ImportError:
    from langchain_core.pydantic_v1 import BaseModel, Field


# 方式1：使用@tool装饰器
@tool
def text_analyzer(text: str) -> str:
    """
    文本分析工具
    
    Args:
        text: 要分析的文本
        
    Returns:
        文本分析结果
    """
    word_count = len(text.split())
    char_count = len(text)
    line_count = len(text.split('\n'))
    
    return f"""文本分析结果：
- 字符数：{char_count}
- 单词数：{word_count}
- 行数：{line_count}
- 平均单词长度：{char_count/word_count if word_count > 0 else 0:.2f}
"""


# 方式2：使用StructuredTool.from_function
class PasswordGeneratorInput(BaseModel):
    """密码生成器输入参数"""
    length: int = Field(default=12, description="密码长度，默认12位")
    include_symbols: bool = Field(default=True, description="是否包含特殊符号")
    include_numbers: bool = Field(default=True, description="是否包含数字")


def generate_password(length: int = 12, include_symbols: bool = True, include_numbers: bool = True) -> str:
    """
    生成安全密码
    
    Args:
        length: 密码长度
        include_symbols: 是否包含特殊符号
        include_numbers: 是否包含数字
        
    Returns:
        生成的密码
    """
    import random
    import string
    
    chars = string.ascii_letters
    if include_numbers:
        chars += string.digits
    if include_symbols:
        chars += "!@#$%^&*"
    
    password = ''.join(random.choice(chars) for _ in range(length))
    return f"生成的密码：{password}"


# 创建StructuredTool
password_generator = StructuredTool.from_function(
    func=generate_password,
    name="password_generator",
    description="生成指定长度和复杂度的安全密码",
    args_schema=PasswordGeneratorInput
)


# 方式3：继承BaseTool类
class TimestampTool(BaseTool):
    """时间戳工具"""
    
    name: str = "timestamp_tool"
    description: str = "获取当前时间戳和格式化时间"
    
    def _run(self, format_type: str = "iso") -> str:
        """
        获取时间戳
        
        Args:
            format_type: 格式类型 (iso, timestamp, readable)
            
        Returns:
            格式化的时间
        """
        from datetime import datetime
        
        now = datetime.now()
        
        if format_type == "iso":
            return f"ISO格式：{now.isoformat()}"
        elif format_type == "timestamp":
            return f"时间戳：{int(now.timestamp())}"
        elif format_type == "readable":
            return f"可读格式：{now.strftime('%Y年%m月%d日 %H:%M:%S')}"
        else:
            return f"未知格式类型：{format_type}"
    
    async def _arun(self, format_type: str = "iso") -> str:
        """异步版本"""
        return self._run(format_type)


# 创建工具实例
timestamp_tool = TimestampTool()


# 导出所有工具（可选，工具加载器会自动发现）
__all__ = [
    "text_analyzer",
    "password_generator", 
    "timestamp_tool"
]
