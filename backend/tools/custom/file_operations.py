"""
自定义工具：文件操作
提供安全的文件读写操作功能
"""

import os
from pathlib import Path
from typing import Optional
from langchain_core.tools import tool
from backend.tools.adapters.universal_tool_adapter import universal_adapter
import logging

logger = logging.getLogger(__name__)

# 安全的工作目录（限制文件操作范围）
SAFE_WORK_DIR = Path("./workspace")
SAFE_WORK_DIR.mkdir(exist_ok=True)


@tool
def read_file(file_path: str, encoding: str = "utf-8") -> str:
    """
    读取文件内容
    
    Args:
        file_path: 文件路径（相对于workspace目录）
        encoding: 文件编码，默认utf-8
    
    Returns:
        文件内容
    """
    try:
        # 确保路径安全
        safe_path = SAFE_WORK_DIR / file_path
        safe_path = safe_path.resolve()
        
        # 检查路径是否在安全目录内
        if not str(safe_path).startswith(str(SAFE_WORK_DIR.resolve())):
            return "错误: 文件路径超出安全范围"
        
        if not safe_path.exists():
            return f"错误: 文件不存在 - {file_path}"
        
        if not safe_path.is_file():
            return f"错误: 不是文件 - {file_path}"
        
        # 读取文件
        with open(safe_path, 'r', encoding=encoding) as f:
            content = f.read()
        
        return f"文件内容 ({file_path}):\n{content}"
        
    except Exception as e:
        return f"读取文件失败: {str(e)}"


@tool
def write_file(file_path: str, content: str, encoding: str = "utf-8") -> str:
    """
    写入文件内容
    
    Args:
        file_path: 文件路径（相对于workspace目录）
        content: 要写入的内容
        encoding: 文件编码，默认utf-8
    
    Returns:
        操作结果
    """
    try:
        # 确保路径安全
        safe_path = SAFE_WORK_DIR / file_path
        safe_path = safe_path.resolve()
        
        # 检查路径是否在安全目录内
        if not str(safe_path).startswith(str(SAFE_WORK_DIR.resolve())):
            return "错误: 文件路径超出安全范围"
        
        # 确保父目录存在
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(safe_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        return f"成功写入文件: {file_path} ({len(content)} 字符)"
        
    except Exception as e:
        return f"写入文件失败: {str(e)}"


@tool
def list_files(directory: str = ".") -> str:
    """
    列出目录中的文件和子目录

    ⚠️ 重要限制：此工具只能访问相对于workspace目录的路径
    - 不能访问绝对路径（如 C:\Users\... 或 /home/...）
    - 只能使用相对路径（如 ".", "subfolder", "data/files"）
    - 工作目录：./workspace

    Args:
        directory: 目录路径，必须是相对路径（相对于workspace目录）
                  例如："." (当前目录), "data" (子目录), "files/documents" (嵌套目录)

    Returns:
        文件和目录列表
    """
    try:
        # 检查是否为绝对路径
        if os.path.isabs(directory):
            return f"""❌ 错误: 不能访问绝对路径 '{directory}'

🔧 此工具只能访问相对于workspace目录的路径。
💡 请使用相对路径，例如：
   - "." (列出workspace根目录)
   - "data" (列出workspace/data目录)
   - "files/documents" (列出workspace/files/documents目录)

📁 当前工作目录: ./workspace"""

        # 确保路径安全
        safe_path = SAFE_WORK_DIR / directory
        safe_path = safe_path.resolve()

        # 检查路径是否在安全目录内
        if not str(safe_path).startswith(str(SAFE_WORK_DIR.resolve())):
            return f"""❌ 错误: 目录路径超出安全范围 '{directory}'

🔧 此工具只能访问workspace目录内的文件。
💡 请使用相对路径，例如：
   - "." (当前目录)
   - "subfolder" (子目录)
   - "data/files" (嵌套目录)"""

        if not safe_path.exists():
            # 提供更有帮助的错误信息
            workspace_contents = []
            try:
                for item in SAFE_WORK_DIR.iterdir():
                    if item.is_dir():
                        workspace_contents.append(f"📁 {item.name}/")
                    else:
                        workspace_contents.append(f"📄 {item.name}")
            except:
                workspace_contents = ["无法读取workspace内容"]

            return f"""❌ 错误: 目录不存在 - '{directory}'

📁 workspace目录当前内容:
{chr(10).join(workspace_contents[:10])}
{('...(还有更多)' if len(workspace_contents) > 10 else '')}

💡 请检查路径是否正确，或使用 "." 查看根目录内容。"""

        if not safe_path.is_dir():
            return f"❌ 错误: '{directory}' 不是目录，而是文件"
        
        # 列出文件
        files = []
        dirs = []
        
        for item in safe_path.iterdir():
            if item.is_file():
                size = item.stat().st_size
                files.append(f"📄 {item.name} ({size} bytes)")
            elif item.is_dir():
                dirs.append(f"📁 {item.name}/")
        
        result = f"目录内容 ({directory}):\n"
        if dirs:
            result += "\n".join(dirs) + "\n"
        if files:
            result += "\n".join(files)
        
        if not dirs and not files:
            result += "目录为空"
        
        return result
        
    except Exception as e:
        return f"列出文件失败: {str(e)}"


# 注册到统一适配器
def register_file_tools():
    """注册文件操作工具到统一适配器"""
    try:
        # 注册读取文件工具
        universal_adapter.register_tool(
            name="read_file",
            function=read_file.func,
            description="读取文件内容（限制在workspace目录内）",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "文件路径，相对于workspace目录"
                    },
                    "encoding": {
                        "type": "string",
                        "description": "文件编码",
                        "default": "utf-8"
                    }
                },
                "required": ["file_path"]
            }
        )
        
        # 注册写入文件工具
        universal_adapter.register_tool(
            name="write_file",
            function=write_file.func,
            description="写入文件内容（限制在workspace目录内）",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "文件路径，相对于workspace目录"
                    },
                    "content": {
                        "type": "string",
                        "description": "要写入的内容"
                    },
                    "encoding": {
                        "type": "string",
                        "description": "文件编码",
                        "default": "utf-8"
                    }
                },
                "required": ["file_path", "content"]
            }
        )
        
        # 注册列出文件工具
        universal_adapter.register_tool(
            name="list_files",
            function=list_files.func,
            description="列出目录中的文件和子目录。⚠️ 只能访问相对路径，不能访问绝对路径（如C:\\或/home/）。工作目录：./workspace",
            parameters={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "目录路径，必须是相对路径（相对于workspace目录）。例如：'.'（当前目录）、'data'（子目录）、'files/docs'（嵌套目录）。不能使用绝对路径。",
                        "default": "."
                    }
                },
                "required": []
            }
        )
    except Exception as e:
        logger.error(f"Failed to register file tools: {e}")


# 自动注册
register_file_tools()

# 导出工具
__all__ = ["read_file", "write_file", "list_files"]
