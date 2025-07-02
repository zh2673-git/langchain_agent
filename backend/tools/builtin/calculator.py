"""
内置工具：计算器
提供基本的数学计算功能
"""

import ast
import operator
from typing import Any, Dict
from langchain_core.tools import tool
from backend.tools.adapters.universal_tool_adapter import universal_adapter


@tool
def simple_calculator(expression: str) -> str:
    """
    计算数学表达式
    
    Args:
        expression: 要计算的数学表达式，例如 "2 + 3 * 4"
    
    Returns:
        计算结果
    """
    try:
        # 安全的数学运算符
        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
            ast.Mod: operator.mod,
        }

        def eval_expr(node):
            if isinstance(node, ast.Constant):  # Python 3.8+
                return node.value
            elif isinstance(node, ast.BinOp):
                return operators[type(node.op)](eval_expr(node.left), eval_expr(node.right))
            elif isinstance(node, ast.UnaryOp):
                return operators[type(node.op)](eval_expr(node.operand))
            else:
                raise TypeError(f"不支持的操作: {type(node)}")

        # 解析并计算表达式
        tree = ast.parse(expression, mode='eval')
        result = eval_expr(tree.body)
        
        return f"计算结果: {result}"
        
    except Exception as e:
        return f"计算错误: {str(e)}"


# 同时注册到统一适配器
def register_calculator_tool():
    """注册计算器工具到统一适配器"""
    try:
        universal_adapter.register_tool(
            name="calculator",
            function=simple_calculator.func,  # 获取原始函数
            description="计算数学表达式，支持基本的四则运算、幂运算和取模运算",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式，例如 '2 + 3 * 4'"
                    }
                },
                "required": ["expression"]
            }
        )
    except Exception as e:
        print(f"Failed to register calculator tool: {e}")


# 自动注册
register_calculator_tool()

# 导出工具
__all__ = ["simple_calculator"]
