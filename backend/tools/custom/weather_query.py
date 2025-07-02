"""
自定义工具：天气查询
提供天气信息查询功能（示例实现）
"""

from typing import Optional
from langchain_core.tools import tool
from backend.tools.adapters.universal_tool_adapter import universal_adapter
import logging

logger = logging.getLogger(__name__)


@tool
def weather_query(location: str, units: str = "metric") -> str:
    """
    查询指定地点的天气信息
    
    Args:
        location: 地点名称，例如 "北京" 或 "Beijing"
        units: 温度单位，metric(摄氏度) 或 imperial(华氏度)
    
    Returns:
        天气信息
    """
    try:
        # 这里是示例实现，实际应该调用天气API
        # 例如 OpenWeatherMap, 和风天气等
        
        # 模拟天气数据
        weather_data = {
            "北京": {"temp": 25, "desc": "晴朗", "humidity": 60},
            "上海": {"temp": 28, "desc": "多云", "humidity": 70},
            "广州": {"temp": 32, "desc": "雷阵雨", "humidity": 85},
            "深圳": {"temp": 30, "desc": "阴天", "humidity": 75},
        }
        
        # 简单的地点匹配
        location_lower = location.lower()
        for city, data in weather_data.items():
            if city in location or location in city:
                temp_unit = "°C" if units == "metric" else "°F"
                temp = data["temp"] if units == "metric" else int(data["temp"] * 9/5 + 32)
                
                return f"{city}天气: {data['desc']}, 温度: {temp}{temp_unit}, 湿度: {data['humidity']}%"
        
        # 如果没有匹配的城市，返回通用信息
        return f"抱歉，暂时无法获取 {location} 的天气信息。请尝试输入主要城市名称，如：北京、上海、广州、深圳。"
        
    except Exception as e:
        return f"天气查询失败: {str(e)}"


def get_weather_with_api(location: str, api_key: Optional[str] = None) -> str:
    """
    使用真实API查询天气（需要API密钥）
    
    Args:
        location: 地点名称
        api_key: API密钥
    
    Returns:
        天气信息
    """
    if not api_key:
        return "需要配置天气API密钥才能使用此功能"
    
    try:
        # 这里可以集成真实的天气API
        # 例如：
        # import requests
        # url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}"
        # response = requests.get(url)
        # data = response.json()
        # return format_weather_data(data)
        
        return f"真实天气API功能需要配置API密钥: {location}"
        
    except Exception as e:
        return f"API天气查询失败: {str(e)}"


# 注册到统一适配器
def register_weather_tool():
    """注册天气查询工具到统一适配器"""
    try:
        universal_adapter.register_tool(
            name="weather_query",
            function=weather_query.func,
            description="查询指定地点的天气信息",
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "地点名称，例如 '北京' 或 'Beijing'"
                    },
                    "units": {
                        "type": "string",
                        "description": "温度单位",
                        "enum": ["metric", "imperial"],
                        "default": "metric"
                    }
                },
                "required": ["location"]
            }
        )
    except Exception as e:
        logger.error(f"Failed to register weather tool: {e}")


# 自动注册
register_weather_tool()

# 导出工具
__all__ = ["weather_query", "get_weather_with_api"]
