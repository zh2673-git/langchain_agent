"""
内置工具：日期时间
提供当前时间查询和时间格式化功能
"""

from datetime import datetime
import pytz
from typing import Optional
from langchain_core.tools import tool
from backend.tools.adapters.universal_tool_adapter import universal_adapter


@tool
def get_current_time(timezone_name: str = "Asia/Shanghai") -> str:
    """
    获取当前时间
    
    Args:
        timezone_name: 时区名称，默认为Asia/Shanghai
    
    Returns:
        当前时间信息
    """
    try:
        # 获取指定时区
        tz = pytz.timezone(timezone_name)
        current_time = datetime.now(tz)
        
        # 格式化时间
        formatted_time = current_time.strftime("%Y年%m月%d日 %H:%M:%S")
        weekday = current_time.strftime("%A")
        
        # 中文星期映射
        weekday_map = {
            "Monday": "星期一",
            "Tuesday": "星期二", 
            "Wednesday": "星期三",
            "Thursday": "星期四",
            "Friday": "星期五",
            "Saturday": "星期六",
            "Sunday": "星期日"
        }
        
        chinese_weekday = weekday_map.get(weekday, weekday)
        
        return f"当前时间: {formatted_time} {chinese_weekday} (时区: {timezone_name})"
        
    except Exception as e:
        return f"获取时间失败: {str(e)}"


@tool
def format_timestamp(timestamp: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化时间戳
    
    Args:
        timestamp: 时间戳（秒）
        format_str: 格式字符串
    
    Returns:
        格式化后的时间
    """
    try:
        # 转换时间戳
        ts = float(timestamp)
        dt = datetime.fromtimestamp(ts)
        
        return f"格式化时间: {dt.strftime(format_str)}"
        
    except Exception as e:
        return f"时间格式化失败: {str(e)}"


# 注册到统一适配器
def register_datetime_tools():
    """注册时间工具到统一适配器"""
    try:
        # 注册当前时间工具
        universal_adapter.register_tool(
            name="get_current_time",
            function=get_current_time.func,
            description="获取当前日期和时间，支持不同时区",
            parameters={
                "type": "object",
                "properties": {
                    "timezone_name": {
                        "type": "string",
                        "description": "时区名称，例如 'Asia/Shanghai', 'UTC', 'America/New_York'",
                        "default": "Asia/Shanghai"
                    }
                },
                "required": []
            }
        )
        
        # 注册时间戳格式化工具
        universal_adapter.register_tool(
            name="format_timestamp",
            function=format_timestamp.func,
            description="将时间戳转换为可读的时间格式",
            parameters={
                "type": "object",
                "properties": {
                    "timestamp": {
                        "type": "string",
                        "description": "Unix时间戳（秒）"
                    },
                    "format_str": {
                        "type": "string",
                        "description": "时间格式字符串，例如 '%Y-%m-%d %H:%M:%S'",
                        "default": "%Y-%m-%d %H:%M:%S"
                    }
                },
                "required": ["timestamp"]
            }
        )
    except Exception as e:
        print(f"Failed to register datetime tools: {e}")


# 自动注册
register_datetime_tools()

# 导出工具
__all__ = ["get_current_time", "format_timestamp"]
