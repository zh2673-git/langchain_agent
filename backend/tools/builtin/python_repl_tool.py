"""
Python REPL工具 - LangChain内置工具
提供Python代码执行环境
"""

from langchain_core.tools import tool
import sys
import io
import contextlib
from typing import Any

# 尝试导入PythonREPLTool，如果失败则使用自定义实现
try:
    from langchain_community.tools import PythonREPLTool
    _python_repl = PythonREPLTool()
    _has_repl_tool = True
except ImportError:
    _python_repl = None
    _has_repl_tool = False

@tool
def python_repl_tool(code: str) -> str:
    """执行Python代码并返回结果

    Args:
        code: 要执行的Python代码

    Returns:
        str: 代码执行结果或错误信息

    Examples:
        - python_repl_tool("print('Hello World')")
        - python_repl_tool("import math; print(math.sqrt(16))")
        - python_repl_tool("x = [1,2,3,4]; print(sum(x))")
    """
    try:
        if _has_repl_tool and _python_repl:
            # 使用LangChain的PythonREPLTool
            result = _python_repl.run(code)
            return str(result) if result else "代码执行完成，无输出"
        else:
            # 使用自定义实现
            return safe_python_exec(code)
    except Exception as e:
        return f"执行错误: {str(e)}"

@tool  
def safe_python_exec(code: str) -> str:
    """安全执行Python代码（受限环境）
    
    Args:
        code: 要执行的Python代码
        
    Returns:
        str: 代码执行结果或错误信息
    """
    try:
        # 创建受限的执行环境
        safe_globals = {
            '__builtins__': {
                'print': print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'range': range,
                'sum': sum,
                'max': max,
                'min': min,
                'abs': abs,
                'round': round,
                'sorted': sorted,
                'reversed': reversed,
                'enumerate': enumerate,
                'zip': zip,
            },
            'math': __import__('math'),
            'datetime': __import__('datetime'),
            'json': __import__('json'),
            're': __import__('re'),
        }
        
        # 捕获输出
        output_buffer = io.StringIO()
        
        with contextlib.redirect_stdout(output_buffer):
            exec(code, safe_globals, {})
        
        result = output_buffer.getvalue()
        return result if result.strip() else "代码执行完成，无输出"
        
    except Exception as e:
        return f"执行错误: {str(e)}"

@tool
def python_calculator(expression: str) -> str:
    """使用Python计算数学表达式
    
    Args:
        expression: 数学表达式
        
    Returns:
        str: 计算结果
        
    Examples:
        - python_calculator("2 + 3 * 4")
        - python_calculator("math.sqrt(16) + math.pi")
        - python_calculator("sum([1,2,3,4,5])")
    """
    try:
        # 安全的数学计算环境
        safe_dict = {
            '__builtins__': {},
            'math': __import__('math'),
            'abs': abs,
            'round': round,
            'sum': sum,
            'max': max,
            'min': min,
            'pow': pow,
            'len': len,
        }
        
        result = eval(expression, safe_dict, {})
        return str(result)
        
    except Exception as e:
        return f"计算错误: {str(e)}"
