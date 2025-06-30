"""
使用 LangChain 原生 @tool 装饰器的文件操作工具
"""
import os
import platform
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.tools import tool

from ...utils.logger import get_logger

logger = get_logger(__name__)


def _get_safe_path(path_name: str) -> Path:
    """获取安全的系统路径"""
    system = platform.system().lower()

    # 处理预定义的快捷路径
    if path_name.lower() in ["desktop", "桌面"]:
        if system == "windows":
            return Path.home() / "Desktop"
        else:
            return Path.home() / "Desktop"
    elif path_name.lower() in ["documents", "文档"]:
        if system == "windows":
            return Path.home() / "Documents"
        else:
            return Path.home() / "Documents"
    elif path_name.lower() in ["downloads", "下载"]:
        return Path.home() / "Downloads"
    elif path_name.lower() in ["home", "主目录"]:
        return Path.home()
    else:
        # 尝试解析为实际路径
        try:
            # 处理绝对路径
            if os.path.isabs(path_name):
                target_path = Path(path_name)
                if target_path.exists():
                    return target_path
                else:
                    logger.warning(f"Path does not exist: {path_name}")
                    return Path.home() / "Desktop"

            # 处理相对路径（相对于用户主目录）
            target_path = Path.home() / path_name
            if target_path.exists():
                return target_path

            # 处理驱动器路径（Windows）
            if system == "windows" and len(path_name) >= 2 and path_name[1] == ":":
                target_path = Path(path_name)
                if target_path.exists():
                    return target_path

            # 如果路径不存在，记录警告并返回默认路径
            logger.warning(f"Path not found: {path_name}, using desktop as default")
            return Path.home() / "Desktop"

        except Exception as e:
            logger.error(f"Error parsing path {path_name}: {e}")
            return Path.home() / "Desktop"


@tool
def list_files(path: str = "desktop", show_hidden: bool = False) -> str:
    """列出指定目录中的文件和文件夹

    Args:
        path: 目录路径，支持以下格式：
              - 快捷名称: desktop, documents, downloads, home
              - 绝对路径: C:/Users/username/folder (Windows) 或 /home/username/folder (Linux/Mac)
              - 相对路径: folder_name (相对于用户主目录)
              - 驱动器: D:, E: 等 (Windows)
        show_hidden: 是否显示隐藏文件，默认False

    Returns:
        目录内容的文本描述
    """
    try:
        target_path = _get_safe_path(path)
        
        if not target_path.exists():
            return f"路径不存在: {target_path}"
        
        if not target_path.is_dir():
            return f"不是目录: {target_path}"
        
        items = []
        try:
            for item in target_path.iterdir():
                if not show_hidden and item.name.startswith('.'):
                    continue
                
                if item.is_dir():
                    items.append(f"📁 {item.name}/")
                else:
                    size = item.stat().st_size
                    size_str = _format_file_size(size)
                    items.append(f"📄 {item.name} ({size_str})")
        except PermissionError:
            return f"没有权限访问目录: {target_path}"
        
        if not items:
            return f"目录为空: {target_path}"
        
        result = f"目录内容 ({target_path}):\n\n"
        result += "\n".join(sorted(items))
        return result
        
    except Exception as e:
        logger.error(f"List files failed: {e}")
        return f"列出文件失败: {str(e)}"


@tool
def read_file(file_path: str, max_lines: int = 100) -> str:
    """读取文件内容
    
    Args:
        file_path: 文件路径
        max_lines: 最大读取行数，默认100行
    
    Returns:
        文件内容
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            return f"文件不存在: {file_path}"
        
        if not path.is_file():
            return f"不是文件: {file_path}"
        
        # 检查文件大小
        size = path.stat().st_size
        if size > 1024 * 1024:  # 1MB
            return f"文件太大，无法读取: {file_path} ({_format_file_size(size)})"
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        lines.append(f"\n... (文件还有更多内容，已截断到 {max_lines} 行)")
                        break
                    lines.append(line.rstrip())
                
                content = "\n".join(lines)
                return f"文件内容 ({file_path}):\n\n{content}"
                
        except UnicodeDecodeError:
            return f"无法读取文件，可能是二进制文件: {file_path}"
        except PermissionError:
            return f"没有权限读取文件: {file_path}"
        
    except Exception as e:
        logger.error(f"Read file failed: {e}")
        return f"读取文件失败: {str(e)}"


@tool
def get_file_info(file_path: str) -> str:
    """获取文件或目录的详细信息
    
    Args:
        file_path: 文件或目录路径
    
    Returns:
        文件信息的文本描述
    """
    try:
        path = Path(file_path)
        
        if not path.exists():
            return f"路径不存在: {file_path}"
        
        stat = path.stat()
        
        info = [
            f"路径: {path.absolute()}",
            f"名称: {path.name}",
            f"类型: {'目录' if path.is_dir() else '文件'}",
            f"大小: {_format_file_size(stat.st_size)}",
            f"创建时间: {_format_timestamp(stat.st_ctime)}",
            f"修改时间: {_format_timestamp(stat.st_mtime)}",
            f"访问时间: {_format_timestamp(stat.st_atime)}"
        ]
        
        if path.is_file():
            info.append(f"扩展名: {path.suffix}")
        
        return "文件信息:\n\n" + "\n".join(info)
        
    except Exception as e:
        logger.error(f"Get file info failed: {e}")
        return f"获取文件信息失败: {str(e)}"


def _format_file_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _format_timestamp(timestamp: float) -> str:
    """格式化时间戳"""
    import datetime
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# 兼容性包装类
from ...base.tool_base import ToolBase, ToolSchema, ToolParameter, ToolResult, ToolType

class NativeFileTool(ToolBase):
    """使用原生 @tool 装饰器的文件工具包装类"""
    
    def __init__(self):
        super().__init__(
            name="file_tool",
            description="文件和目录操作工具。用法示例：查看桌面文件path=desktop，查看文档目录path=documents，查看指定目录path=C:/Users，读取文件action=read+path=文件路径。默认操作是列出目录内容。",
            tool_type=ToolType.FILE
        )
        self.list_files_tool = list_files
        self.read_file_tool = read_file
        self.get_file_info_tool = get_file_info
    
    async def initialize(self) -> bool:
        """初始化工具"""
        self._initialized = True
        logger.info("NativeFileTool initialized successfully")
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
                        name="action",
                        type="string",
                        description="操作类型：list列出目录，read读取文件，info获取文件信息",
                        required=False,
                        enum=["list", "read", "info"],
                        default="list"
                    ),
                    ToolParameter(
                        name="path",
                        type="string",
                        description="文件或目录路径，支持desktop、documents等快捷路径",
                        required=True
                    ),
                    ToolParameter(
                        name="show_hidden",
                        type="boolean",
                        description="是否显示隐藏文件",
                        required=False,
                        default=False
                    ),
                    ToolParameter(
                        name="max_lines",
                        type="number",
                        description="读取文件时的最大行数限制",
                        required=False,
                        default=100
                    )
                ]
            )
        return self._schema
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行文件操作"""
        try:
            self.validate_parameters(kwargs)
            
            action = kwargs.get("action", "list")  # 默认为list操作
            path = kwargs["path"]
            
            if action == "list":
                show_hidden = kwargs.get("show_hidden", False)
                result = self.list_files_tool.invoke({
                    "path": path,
                    "show_hidden": show_hidden
                })
            elif action == "read":
                max_lines = kwargs.get("max_lines", 100)
                result = self.read_file_tool.invoke({
                    "file_path": path,
                    "max_lines": max_lines
                })
            elif action == "info":
                result = self.get_file_info_tool.invoke({
                    "file_path": path
                })
            else:
                return ToolResult(
                    success=False,
                    error=f"不支持的操作: {action}"
                )
            
            return ToolResult(
                success=True,
                result=result,
                metadata={
                    "action": action,
                    "path": path,
                    "tool_type": "native_langchain"
                }
            )
            
        except Exception as e:
            logger.error(f"Native file tool execution failed: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    def get_list_files_tool(self):
        """获取列出文件工具"""
        return self.list_files_tool
    
    def get_read_file_tool(self):
        """获取读取文件工具"""
        return self.read_file_tool
    
    def get_file_info_tool(self):
        """获取文件信息工具"""
        return self.get_file_info_tool
