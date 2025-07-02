"""
OpenWebUI工具索引
自动生成的索引文件 - 请勿手动修改

包含 15 个工具:
- calculator: 计算数学表达式，支持基本的四则运算、幂运算和取模运算
- get_current_time: 获取当前日期和时间，支持不同时区
- format_timestamp: 将时间戳转换为可读的时间格式
- web_search: 搜索网络信息，获取实时数据和答案
- wikipedia_search: 搜索Wikipedia文章，获取百科知识
- string_processor: 字符串处理工具，支持大小写转换、反转和长度计算
- list_processor: 处理列表数据，支持排序、去重、计数等操作
- read_file: 读取文件内容（限制在workspace目录内）
- write_file: 写入文件内容（限制在workspace目录内）
- list_files: 列出目录中的文件和子目录
- extract_information: 从文本中提取特定信息，如邮箱、网址、电话号码等
- generate_uuid: 生成UUID（通用唯一标识符）
- date_calculator: 日期计算器，支持日期加减和差值计算
- weather_query: 查询指定地点的天气信息
- calculate: 计算数学表达式，支持基本的四则运算、幂运算和取模运算
"""

# 工具列表
AVAILABLE_TOOLS = [
    "calculator",
    "get_current_time",
    "format_timestamp",
    "web_search",
    "wikipedia_search",
    "string_processor",
    "list_processor",
    "read_file",
    "write_file",
    "list_files",
    "extract_information",
    "generate_uuid",
    "date_calculator",
    "weather_query",
    "calculate"
]

# 工具描述
TOOL_DESCRIPTIONS = {
    "calculator": "计算数学表达式，支持基本的四则运算、幂运算和取模运算",
    "get_current_time": "获取当前日期和时间，支持不同时区",
    "format_timestamp": "将时间戳转换为可读的时间格式",
    "web_search": "搜索网络信息，获取实时数据和答案",
    "wikipedia_search": "搜索Wikipedia文章，获取百科知识",
    "string_processor": "字符串处理工具，支持大小写转换、反转和长度计算",
    "list_processor": "处理列表数据，支持排序、去重、计数等操作",
    "read_file": "读取文件内容（限制在workspace目录内）",
    "write_file": "写入文件内容（限制在workspace目录内）",
    "list_files": "列出目录中的文件和子目录",
    "extract_information": "从文本中提取特定信息，如邮箱、网址、电话号码等",
    "generate_uuid": "生成UUID（通用唯一标识符）",
    "date_calculator": "日期计算器，支持日期加减和差值计算",
    "weather_query": "查询指定地点的天气信息",
    "calculate": "计算数学表达式，支持基本的四则运算、幂运算和取模运算",
}
