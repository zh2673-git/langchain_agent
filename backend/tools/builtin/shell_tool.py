"""
Shell工具 - LangChain内置工具
提供系统命令执行能力
"""

from langchain_core.tools import tool
import subprocess
import platform
import os
from typing import Any

# 尝试导入ShellTool，如果失败则使用自定义实现
try:
    from langchain_community.tools import ShellTool
    _shell_tool = ShellTool()
    _has_shell_tool = True
except ImportError:
    _shell_tool = None
    _has_shell_tool = False

@tool
def shell_tool(command: str) -> str:
    """执行系统命令

    Args:
        command: 要执行的系统命令

    Returns:
        str: 命令执行结果或错误信息

    Examples:
        - shell_tool("ls -la") (Linux/Mac)
        - shell_tool("dir") (Windows)
        - shell_tool("python --version")
    """
    try:
        if _has_shell_tool and _shell_tool:
            # 使用LangChain的ShellTool
            result = _shell_tool.run(command)
            return str(result) if result else "命令执行完成，无输出"
        else:
            # 使用自定义实现
            return safe_shell_exec(command)
    except Exception as e:
        return f"执行错误: {str(e)}"

@tool
def safe_shell_exec(command: str) -> str:
    """安全执行系统命令（受限命令集）
    
    Args:
        command: 要执行的系统命令
        
    Returns:
        str: 命令执行结果或错误信息
    """
    try:
        # 定义允许的安全命令
        safe_commands = {
            'windows': [
                'dir', 'type', 'echo', 'date', 'time', 'ver', 'whoami',
                'systeminfo', 'tasklist', 'ipconfig', 'ping', 'nslookup',
                'python', 'pip', 'conda', 'git', 'node', 'npm'
            ],
            'linux': [
                'ls', 'cat', 'echo', 'date', 'whoami', 'pwd', 'uname',
                'ps', 'top', 'df', 'free', 'ping', 'nslookup',
                'python', 'pip', 'conda', 'git', 'node', 'npm'
            ],
            'darwin': [  # macOS
                'ls', 'cat', 'echo', 'date', 'whoami', 'pwd', 'uname',
                'ps', 'top', 'df', 'ping', 'nslookup',
                'python', 'pip', 'conda', 'git', 'node', 'npm'
            ]
        }
        
        system = platform.system().lower()
        allowed_commands = safe_commands.get(system, safe_commands['linux'])
        
        # 检查命令是否安全
        cmd_parts = command.split()
        if not cmd_parts:
            return "错误: 空命令"
            
        base_command = cmd_parts[0]
        if base_command not in allowed_commands:
            return f"错误: 不允许执行命令 '{base_command}'"
        
        # 执行命令
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30  # 30秒超时
        )
        
        if result.returncode == 0:
            return result.stdout if result.stdout else "命令执行成功，无输出"
        else:
            return f"命令执行失败 (退出码: {result.returncode}): {result.stderr}"
            
    except subprocess.TimeoutExpired:
        return "错误: 命令执行超时"
    except Exception as e:
        return f"执行错误: {str(e)}"

@tool
def system_info() -> str:
    """获取系统信息
    
    Returns:
        str: 系统信息
    """
    try:
        info = {
            "操作系统": platform.system(),
            "系统版本": platform.release(),
            "架构": platform.machine(),
            "处理器": platform.processor(),
            "Python版本": platform.python_version(),
            "当前目录": os.getcwd(),
            "用户名": os.getenv('USERNAME') or os.getenv('USER', 'unknown')
        }
        
        result = "系统信息:\n"
        for key, value in info.items():
            result += f"- {key}: {value}\n"
            
        return result
        
    except Exception as e:
        return f"获取系统信息失败: {str(e)}"
