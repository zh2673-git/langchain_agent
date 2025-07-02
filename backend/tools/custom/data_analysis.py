"""
自定义工具：数据分析
提供基本的数据分析和统计功能
"""

import json
import statistics
from typing import List, Dict, Any
from langchain_core.tools import tool
from backend.tools.adapters.universal_tool_adapter import universal_adapter
import logging

logger = logging.getLogger(__name__)


@tool
def analyze_numbers(numbers_str: str) -> str:
    """
    分析数字列表的统计信息
    
    Args:
        numbers_str: 数字列表，用逗号分隔，如 "1,2,3,4,5"
    
    Returns:
        统计分析结果
    """
    try:
        # 解析数字
        numbers = [float(x.strip()) for x in numbers_str.split(',') if x.strip()]
        
        if not numbers:
            return "❌ 未提供有效数字"
        
        # 基本统计
        count = len(numbers)
        total = sum(numbers)
        mean = statistics.mean(numbers)
        median = statistics.median(numbers)
        
        # 范围统计
        min_val = min(numbers)
        max_val = max(numbers)
        range_val = max_val - min_val
        
        # 高级统计
        try:
            mode = statistics.mode(numbers)
        except statistics.StatisticsError:
            mode = "无众数"
        
        if count > 1:
            stdev = statistics.stdev(numbers)
            variance = statistics.variance(numbers)
        else:
            stdev = 0
            variance = 0
        
        result = f"""📊 数字统计分析:

📈 基本统计:
- 数量: {count}
- 总和: {total:.2f}
- 平均值: {mean:.2f}
- 中位数: {median:.2f}
- 众数: {mode}

📏 范围统计:
- 最小值: {min_val}
- 最大值: {max_val}
- 范围: {range_val:.2f}

📐 分布统计:
- 标准差: {stdev:.2f}
- 方差: {variance:.2f}

🔢 原始数据: {numbers_str}"""
        
        return result
        
    except ValueError as e:
        return f"❌ 数字解析失败: {str(e)}，请确保输入格式正确，如: 1,2,3,4,5"
    except Exception as e:
        return f"❌ 分析失败: {str(e)}"


@tool
def json_formatter(json_str: str, action: str = "format") -> str:
    """
    JSON数据处理工具
    
    Args:
        json_str: JSON字符串
        action: 操作类型 (format, validate, minify, keys)
    
    Returns:
        处理结果
    """
    try:
        if action == "validate":
            try:
                json.loads(json_str)
                return "✅ JSON格式有效"
            except json.JSONDecodeError as e:
                return f"❌ JSON格式无效: {str(e)}"
        
        # 解析JSON
        data = json.loads(json_str)
        
        if action == "format":
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            return f"📝 格式化的JSON:\n```json\n{formatted}\n```"
        
        elif action == "minify":
            minified = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
            return f"🗜️ 压缩的JSON:\n{minified}"
        
        elif action == "keys":
            if isinstance(data, dict):
                keys = list(data.keys())
                return f"🔑 JSON键列表 ({len(keys)}个):\n" + '\n'.join(f"- {key}" for key in keys)
            else:
                return f"📋 JSON类型: {type(data).__name__}"
        
        else:
            return f"❌ 未知操作: {action}，支持: format, validate, minify, keys"
        
    except json.JSONDecodeError as e:
        return f"❌ JSON解析失败: {str(e)}"
    except Exception as e:
        return f"❌ 处理失败: {str(e)}"


def list_processor(items_str: str, operation: str = "sort") -> str:
    """
    列表处理工具
    
    Args:
        items_str: 列表项，用逗号分隔
        operation: 操作类型 (sort, reverse, unique, count, shuffle)
    
    Returns:
        处理结果
    """
    try:
        # 解析列表项
        items = [item.strip() for item in items_str.split(',') if item.strip()]
        
        if not items:
            return "❌ 未提供有效列表项"
        
        if operation == "sort":
            sorted_items = sorted(items)
            return f"📊 排序后的列表:\n" + '\n'.join(f"{i+1}. {item}" for i, item in enumerate(sorted_items))
        
        elif operation == "reverse":
            reversed_items = list(reversed(items))
            return f"🔄 反转后的列表:\n" + '\n'.join(f"{i+1}. {item}" for i, item in enumerate(reversed_items))
        
        elif operation == "unique":
            unique_items = list(dict.fromkeys(items))  # 保持顺序的去重
            return f"🎯 去重后的列表 ({len(unique_items)}个):\n" + '\n'.join(f"{i+1}. {item}" for i, item in enumerate(unique_items))
        
        elif operation == "count":
            count_dict = {}
            for item in items:
                count_dict[item] = count_dict.get(item, 0) + 1
            
            result = f"📊 项目计数 (总计{len(items)}个):\n"
            for item, count in sorted(count_dict.items(), key=lambda x: x[1], reverse=True):
                result += f"- {item}: {count}次\n"
            return result.strip()
        
        elif operation == "shuffle":
            import random
            shuffled_items = items.copy()
            random.shuffle(shuffled_items)
            return f"🎲 随机排序的列表:\n" + '\n'.join(f"{i+1}. {item}" for i, item in enumerate(shuffled_items))
        
        else:
            return f"❌ 未知操作: {operation}，支持: sort, reverse, unique, count, shuffle"
        
    except Exception as e:
        return f"❌ 处理失败: {str(e)}"


# 注册到统一适配器
def register_data_analysis_tools():
    """注册数据分析工具到统一适配器"""
    try:
        # 注册列表处理工具
        universal_adapter.register_tool(
            name="list_processor",
            function=list_processor,
            description="处理列表数据，支持排序、去重、计数等操作",
            parameters={
                "type": "object",
                "properties": {
                    "items_str": {
                        "type": "string",
                        "description": "列表项，用逗号分隔，如 'apple,banana,orange'"
                    },
                    "operation": {
                        "type": "string",
                        "description": "操作类型",
                        "enum": ["sort", "reverse", "unique", "count", "shuffle"],
                        "default": "sort"
                    }
                },
                "required": ["items_str"]
            }
        )
        
        logger.info("Data analysis tools registered successfully")
    except Exception as e:
        logger.error(f"Failed to register data analysis tools: {e}")


# 自动注册
register_data_analysis_tools()

# 导出工具
__all__ = ["analyze_numbers", "json_formatter", "list_processor"]
