"""
使用 LangChain 原生 @tool 装饰器的计算器工具
这是推荐的工具实现方式
"""
import math
import re
from typing import Union
from decimal import Decimal, getcontext
from langchain_core.tools import tool

# 设置默认精度
getcontext().prec = 10

# 安全的数学函数
SAFE_FUNCTIONS = {
    'abs': abs, 'round': round, 'min': min, 'max': max, 'sum': sum, 'pow': pow,
    'sqrt': math.sqrt, 'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
    'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
    'log': math.log, 'log10': math.log10, 'exp': math.exp,
    'ceil': math.ceil, 'floor': math.floor, 'pi': math.pi, 'e': math.e
}

def _clean_expression(expression: str) -> str:
    """清理数学表达式"""
    expression = expression.replace(" ", "")
    replacements = {
        "×": "*", "÷": "/", "²": "**2", "³": "**3", "π": "pi", "√": "sqrt"
    }
    for old, new in replacements.items():
        expression = expression.replace(old, new)
    return expression

def _is_safe_expression(expression: str) -> bool:
    """检查表达式是否安全"""
    dangerous_keywords = [
        "import", "exec", "eval", "__", "open", "file", "input", "raw_input",
        "compile", "reload", "globals", "locals", "vars", "dir", "help",
        "quit", "exit", "copyright", "credits", "license"
    ]
    
    expression_lower = expression.lower()
    for keyword in dangerous_keywords:
        if keyword in expression_lower:
            return False
    
    # 只允许数字、运算符、括号和安全函数
    allowed_pattern = r'^[0-9+\-*/().a-zA-Z_,\s]+$'
    return bool(re.match(allowed_pattern, expression))

def _format_result(result: Union[int, float, Decimal], format_type: str, precision: int) -> str:
    """格式化计算结果"""
    if format_type == "decimal":
        return f"{result:.{precision}f}" if isinstance(result, float) else str(result)
    elif format_type == "scientific":
        return f"{result:.{precision}e}" if isinstance(result, (int, float)) else str(result)
    elif format_type == "fraction":
        try:
            from fractions import Fraction
            if isinstance(result, (int, float)):
                frac = Fraction(result).limit_denominator(1000)
                return str(frac)
        except:
            pass
        return str(result)
    else:  # auto format
        if isinstance(result, int):
            return str(result)
        elif isinstance(result, float):
            if result.is_integer():
                return str(int(result))
            elif abs(result) >= 1e6 or (abs(result) < 1e-3 and result != 0):
                return f"{result:.{precision}e}"
            else:
                return f"{result:.{precision}f}".rstrip('0').rstrip('.')
        else:
            return str(result)


@tool
def calculator(expression: str, precision: int = 10, format_type: str = "auto") -> str:
    """执行数学计算，支持基本运算、函数和复杂表达式
    
    Args:
        expression: 要计算的数学表达式，支持 +, -, *, /, **, (), 以及数学函数如 sin, cos, sqrt 等
        precision: 计算精度（小数位数），默认10位
        format_type: 结果格式，可选值：auto（自动）, decimal（小数）, scientific（科学计数法）, fraction（分数）
    
    Returns:
        计算结果的字符串表示
        
    Examples:
        calculator("2 + 3 * 4")  # 返回 "14"
        calculator("sqrt(16)")   # 返回 "4.0"
        calculator("sin(pi/2)")  # 返回 "1.0"
    """
    try:
        # 设置精度
        getcontext().prec = precision
        
        # 清理表达式
        cleaned_expression = _clean_expression(expression)
        
        # 安全检查
        if not _is_safe_expression(cleaned_expression):
            return "错误：表达式包含不安全的操作或字符"
        
        # 创建安全的命名空间并计算
        safe_dict = {"__builtins__": {}, **SAFE_FUNCTIONS}
        result = eval(cleaned_expression, safe_dict)
        
        # 格式化结果
        formatted_result = _format_result(result, format_type, precision)
        return formatted_result
        
    except ZeroDivisionError:
        return "错误：除零错误"
    except ValueError as e:
        return f"错误：数值错误 - {str(e)}"
    except SyntaxError:
        return "错误：表达式语法错误"
    except Exception as e:
        return f"计算错误：{str(e)}"


@tool
def math_help() -> str:
    """获取数学计算器的帮助信息
    
    Returns:
        支持的数学函数和操作符列表
    """
    help_text = """
数学计算器支持的功能：

基本运算符：
- 加法：+
- 减法：-
- 乘法：*
- 除法：/
- 幂运算：**
- 括号：()

数学函数：
- sqrt(x)：平方根
- sin(x), cos(x), tan(x)：三角函数
- asin(x), acos(x), atan(x)：反三角函数
- log(x)：自然对数
- log10(x)：常用对数
- exp(x)：指数函数
- abs(x)：绝对值
- ceil(x), floor(x)：向上/向下取整
- round(x)：四舍五入

数学常数：
- pi：圆周率
- e：自然常数

示例：
- calculator("2 + 3 * 4")
- calculator("sqrt(16)")
- calculator("sin(pi/2)")
- calculator("log(e)")
"""
    return help_text.strip()


# 为了兼容现有系统，也提供传统的工具类
from ...base.tool_base import ToolBase, ToolSchema, ToolParameter, ToolResult, ToolType
from ...utils.logger import get_logger

logger = get_logger(__name__)


class NativeCalculatorTool(ToolBase):
    """使用原生 @tool 装饰器的计算器工具包装类"""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="执行数学计算，支持基本运算、函数和复杂表达式",
            tool_type=ToolType.CALCULATOR
        )
        # 存储原生工具引用
        self.native_tool = calculator
        self.help_tool = math_help
    
    async def initialize(self) -> bool:
        """初始化工具"""
        self._initialized = True
        logger.info("NativeCalculatorTool initialized successfully")
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
                        name="expression",
                        type="string",
                        description="要计算的数学表达式",
                        required=True
                    ),
                    ToolParameter(
                        name="precision",
                        type="number",
                        description="计算精度（小数位数）",
                        required=False,
                        default=10
                    ),
                    ToolParameter(
                        name="format_type",
                        type="string",
                        description="结果格式",
                        required=False,
                        default="auto",
                        enum=["auto", "decimal", "scientific", "fraction"]
                    )
                ]
            )
        return self._schema
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行计算"""
        try:
            # 验证参数
            self.validate_parameters(kwargs)
            
            expression = kwargs["expression"]
            precision = kwargs.get("precision", 10)
            format_type = kwargs.get("format_type", "auto")
            
            # 调用原生工具
            result = self.native_tool.invoke({
                "expression": expression,
                "precision": precision,
                "format_type": format_type
            })
            
            return ToolResult(
                success=True,
                result=result,
                metadata={
                    "expression": expression,
                    "precision": precision,
                    "format_type": format_type,
                    "tool_type": "native_langchain"
                }
            )
            
        except Exception as e:
            logger.error(f"Native calculator execution failed: {e}")
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    def get_native_tool(self):
        """获取原生 LangChain 工具"""
        return self.native_tool
    
    def get_help_tool(self):
        """获取帮助工具"""
        return self.help_tool
