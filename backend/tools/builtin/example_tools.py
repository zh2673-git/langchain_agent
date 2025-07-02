"""
示例工具 - 展示两种LangChain工具定义方式

完全按照LangChain官方标准实现：
1. @tool装饰器：最简单的方式，适合简单工具
2. StructuredTool.from_function：支持复杂参数定义和验证

这两种方式覆盖了大部分工具开发需求
"""

from typing import Dict, Any, Optional, List
from langchain_core.tools import tool, StructuredTool
try:
    from pydantic import BaseModel, Field
except ImportError:
    from langchain_core.pydantic_v1 import BaseModel, Field


# 方式1：使用@tool装饰器（最简单）
@tool
def simple_calculator(expression: str) -> str:
    """
    简单计算器工具
    
    Args:
        expression: 数学表达式，如 "2 + 3 * 4"
        
    Returns:
        计算结果
    """
    try:
        # 安全的数学表达式计算
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in expression):
            return "错误：表达式包含不允许的字符"
        
        result = eval(expression)
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


# 方式2：使用StructuredTool.from_function（支持复杂参数）
class WeatherInput(BaseModel):
    """天气查询输入参数"""
    city: str = Field(description="城市名称，如：北京、上海")
    date: Optional[str] = Field(default=None, description="日期，格式：YYYY-MM-DD，默认为今天")


def get_weather(city: str, date: Optional[str] = None) -> str:
    """
    获取天气信息
    
    Args:
        city: 城市名称
        date: 日期（可选）
        
    Returns:
        天气信息
    """
    # 模拟天气数据
    weather_data = {
        "北京": "晴天，温度 15-25°C",
        "上海": "多云，温度 18-28°C",
        "广州": "雨天，温度 20-30°C"
    }
    
    weather = weather_data.get(city, "未知城市")
    date_str = f"，日期：{date}" if date else ""
    
    return f"{city}的天气：{weather}{date_str}"


# 创建StructuredTool
weather_tool = StructuredTool.from_function(
    func=get_weather,
    name="weather_query",
    description="查询指定城市的天气信息",
    args_schema=WeatherInput
)


# 方式3：使用StructuredTool创建文件操作工具
class FileOperationInput(BaseModel):
    """文件操作输入参数"""
    operation: str = Field(description="操作类型：read, write, list")
    path: str = Field(description="文件或目录路径，必须是相对路径（相对于workspace目录）。例如：'.'（当前目录）、'data'（子目录）、'files/docs'（嵌套目录）。不能使用绝对路径如C:/或/home/")
    content: Optional[str] = Field(default=None, description="写入内容（仅write操作需要）")


def file_operation(operation: str, path: str, content: Optional[str] = None) -> str:
    """
    执行安全的文件操作

    ⚠️ 安全限制：只能访问相对于workspace目录的路径
    - 不能访问绝对路径（如 C:/Users/... 或 /home/...）
    - 只能使用相对路径（如 ".", "data", "files/docs"）
    - 工作目录：./workspace

    Args:
        operation: 操作类型（read, write, list）
        path: 文件路径，必须是相对路径（相对于workspace目录）
        content: 写入内容（仅write操作需要）

    Returns:
        操作结果
    """
    import os
    from pathlib import Path

    # 安全的工作目录
    SAFE_WORK_DIR = Path("./workspace")
    SAFE_WORK_DIR.mkdir(exist_ok=True)

    try:
        # 检查是否为绝对路径
        if os.path.isabs(path):
            error_msg = (
                f"❌ 错误: 不能访问绝对路径 '{path}'\n\n"
                "🔧 此工具只能访问相对于workspace目录的路径。\n"
                "💡 请使用相对路径，例如：\n"
                '   - "." (workspace根目录)\n'
                '   - "data" (workspace/data目录)\n'
                '   - "files/documents" (workspace/files/documents目录)\n\n'
                "📁 当前工作目录: ./workspace\n\n"
                "💡 可用操作:\n"
                '   - operation="list", path="." (列出workspace根目录)\n'
                '   - operation="read", path="README.md" (读取文件)\n'
                '   - operation="write", path="output.txt", content="内容" (写入文件)'
            )
            return error_msg

        # 确保路径安全
        safe_path = SAFE_WORK_DIR / path
        safe_path = safe_path.resolve()

        # 检查路径是否在安全目录内
        if not str(safe_path).startswith(str(SAFE_WORK_DIR.resolve())):
            error_msg = (
                f"❌ 错误: 路径超出安全范围 '{path}'\n\n"
                "🔧 此工具只能访问workspace目录内的文件。\n"
                "💡 请使用相对路径，例如：\n"
                '   - "." (当前目录)\n'
                '   - "subfolder" (子目录)\n'
                '   - "data/files" (嵌套目录)'
            )
            return error_msg

        if operation == "read":
            if not safe_path.exists():
                return f"❌ 错误: 文件不存在 - {path}"
            if not safe_path.is_file():
                return f"❌ 错误: '{path}' 不是文件"

            with open(safe_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"📄 文件内容 ({path}):\n{content}"

        elif operation == "write":
            if content is None:
                return "❌ 错误：写入操作需要提供content参数"

            # 确保父目录存在
            safe_path.parent.mkdir(parents=True, exist_ok=True)

            with open(safe_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"✅ 成功写入文件: {path} ({len(content)} 字符)"

        elif operation == "list":
            if not safe_path.exists():
                # 提供有帮助的错误信息
                workspace_contents = []
                try:
                    for item in SAFE_WORK_DIR.iterdir():
                        if item.is_dir():
                            workspace_contents.append(f"📁 {item.name}/")
                        else:
                            workspace_contents.append(f"📄 {item.name}")
                except:
                    workspace_contents = ["无法读取workspace内容"]

                content_list = "\n".join(workspace_contents[:10])
                more_text = "...(还有更多)" if len(workspace_contents) > 10 else ""
                error_msg = (
                    f"❌ 错误: 目录不存在 - '{path}'\n\n"
                    "📁 workspace目录当前内容:\n"
                    f"{content_list}\n"
                    f"{more_text}\n\n"
                    '💡 请使用 operation="list", path="." 查看根目录内容。'
                )
                return error_msg

            if not safe_path.is_dir():
                return f"❌ 错误: '{path}' 不是目录，而是文件"

            files = []
            dirs = []

            for item in safe_path.iterdir():
                if item.is_file():
                    size = item.stat().st_size
                    files.append(f"📄 {item.name} ({size} bytes)")
                elif item.is_dir():
                    dirs.append(f"📁 {item.name}/")

            result = f"📁 目录内容 ({path}):\n"
            if dirs:
                result += "\n".join(dirs) + "\n"
            if files:
                result += "\n".join(files)

            if not dirs and not files:
                result += "目录为空"

            return result

        else:
            error_msg = (
                f"❌ 错误：不支持的操作类型 '{operation}'\n\n"
                "💡 支持的操作类型:\n"
                '   - "read" - 读取文件内容\n'
                '   - "write" - 写入文件内容\n'
                '   - "list" - 列出目录内容'
            )
            return error_msg

    except Exception as e:
        return f"❌ 文件操作失败：{str(e)}"


# 创建文件操作工具
file_operation_tool = StructuredTool.from_function(
    func=file_operation,
    name="file_operation",
    description="执行安全的文件操作（读取、写入、列出文件）。⚠️ 只能访问相对路径，不能访问绝对路径。工作目录：./workspace",
    args_schema=FileOperationInput
)


# 方式4：使用StructuredTool创建更复杂的工具
class DataAnalysisInput(BaseModel):
    """数据分析输入参数"""
    data: List[float] = Field(description="数字列表，如：[1, 2, 3, 4, 5]")
    operation: str = Field(description="操作类型：sum, avg, max, min, count")


def analyze_data(data: List[float], operation: str) -> str:
    """
    数据分析工具

    Args:
        data: 数字列表
        operation: 操作类型

    Returns:
        分析结果
    """
    try:
        if operation == "sum":
            result = sum(data)
        elif operation == "avg":
            result = sum(data) / len(data) if data else 0
        elif operation == "max":
            result = max(data) if data else 0
        elif operation == "min":
            result = min(data) if data else 0
        elif operation == "count":
            result = len(data)
        else:
            return f"不支持的操作: {operation}"

        return f"数据分析结果 ({operation}): {result}"
    except Exception as e:
        return f"数据分析失败: {str(e)}"


# 创建高级StructuredTool
data_analysis_tool = StructuredTool.from_function(
    func=analyze_data,
    name="data_analysis",
    description="对数字列表进行统计分析，支持求和、平均值、最大值、最小值、计数等操作",
    args_schema=DataAnalysisInput
)


# 工具注册函数
def get_example_tools():
    """获取所有示例工具"""
    return [
        simple_calculator,      # @tool装饰器创建的工具
        weather_tool,          # StructuredTool创建的工具
        file_operation_tool,   # StructuredTool文件操作工具
        data_analysis_tool,    # 高级StructuredTool
    ]


def get_basic_tools():
    """获取基础工具"""
    return [
        simple_calculator,
        weather_tool
    ]


def get_advanced_tools():
    """获取高级工具示例"""
    return [
        file_operation_tool,
        data_analysis_tool
    ]


# 演示如何使用工具管理器
def demo_tool_manager():
    """演示工具管理器的使用"""
    from ..tool_manager import ToolManager
    
    # 创建工具管理器
    manager = ToolManager()
    
    # 添加工具
    for tool in get_example_tools():
        manager.add_tool(tool)
    
    # 添加函数作为工具
    def text_length(text: str) -> str:
        """计算文本长度"""
        return f"文本长度：{len(text)}"
    
    manager.add_function_as_tool(text_length, description="计算文本长度的工具")
    
    # 获取工具信息
    print("工具统计：", manager.get_stats())
    print("工具描述：", manager.get_tools_description())
    
    # 执行工具
    result = manager.execute_tool("simple_calculator", expression="2 + 3")
    print("计算结果：", result)
    
    return manager


if __name__ == "__main__":
    demo_tool_manager()
