"""
演示自定义工具
展示如何使用LangChain @tool装饰器创建自定义工具
"""

from langchain_core.tools import tool
import random
import datetime

@tool
def demo_custom_tool(message: str, repeat_count: int = 1) -> str:
    """演示自定义工具
    
    Args:
        message: 要处理的消息
        repeat_count: 重复次数，默认1次
        
    Returns:
        str: 处理后的消息
        
    Examples:
        - demo_custom_tool("Hello", 3)
        - demo_custom_tool("测试消息")
    """
    try:
        result = []
        for i in range(repeat_count):
            result.append(f"[自定义工具 #{i+1}] {message}")
        
        return "\n".join(result) + f"\n\n✅ 自定义工具执行完成，处理了 {repeat_count} 次"
        
    except Exception as e:
        return f"❌ 自定义工具执行失败: {str(e)}"

@tool
def weather_tool(city: str, unit: str = "celsius") -> str:
    """模拟天气查询工具（演示用）
    
    Args:
        city: 城市名称
        unit: 温度单位，可选值：celsius（摄氏度）, fahrenheit（华氏度）
        
    Returns:
        str: 天气信息
        
    Examples:
        - weather_tool("北京")
        - weather_tool("Shanghai", "fahrenheit")
    """
    try:
        # 模拟天气数据
        weather_conditions = ["晴朗", "多云", "小雨", "阴天", "雾霾"]
        condition = random.choice(weather_conditions)
        
        if unit == "fahrenheit":
            temp = random.randint(32, 95)  # 华氏度
            unit_symbol = "°F"
        else:
            temp = random.randint(0, 35)   # 摄氏度
            unit_symbol = "°C"
        
        humidity = random.randint(30, 90)
        wind_speed = random.randint(5, 25)
        
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        weather_info = f"""
🌤️ {city} 天气信息 ({current_time})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌡️ 温度: {temp}{unit_symbol}
☁️ 天气: {condition}
💧 湿度: {humidity}%
💨 风速: {wind_speed} km/h

⚠️ 注意：这是演示数据，非真实天气信息
        """
        
        return weather_info.strip()
        
    except Exception as e:
        return f"❌ 天气查询失败: {str(e)}"

@tool
def random_quote_tool(category: str = "motivation") -> str:
    """随机名言工具
    
    Args:
        category: 名言类别，可选值：motivation（励志）, wisdom（智慧）, humor（幽默）
        
    Returns:
        str: 随机名言
    """
    try:
        quotes = {
            "motivation": [
                "成功不是终点，失败不是末日，继续前进的勇气才最可贵。",
                "不要等待机会，而要创造机会。",
                "今天的努力，是为了明天的选择。",
                "相信自己，你比想象中更强大。"
            ],
            "wisdom": [
                "知识是力量，但智慧是运用知识的能力。",
                "学而时习之，不亦说乎？",
                "三人行，必有我师焉。",
                "路漫漫其修远兮，吾将上下而求索。"
            ],
            "humor": [
                "程序员的三大美德：懒惰、急躁和傲慢。",
                "代码如诗，但有时候是打油诗。",
                "Bug不是问题，没有Bug才是问题。",
                "世界上有10种人：懂二进制的和不懂二进制的。"
            ]
        }
        
        if category not in quotes:
            category = "motivation"
        
        quote = random.choice(quotes[category])
        return f"💭 {category.title()} Quote:\n\n\"{quote}\"\n\n✨ 来自自定义名言工具"
        
    except Exception as e:
        return f"❌ 名言获取失败: {str(e)}"
