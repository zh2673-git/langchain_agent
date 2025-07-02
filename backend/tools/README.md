# 🔧 统一工具系统

## 📁 目录结构

```
backend/tools/
├── adapters/                    # 工具适配器
│   ├── universal_tool_adapter.py   # 统一工具适配器
│   └── openwebui_exporter.py       # OpenWebUI导出器
├── builtin/                     # LangChain内置工具
│   ├── calculator.py               # 计算器工具
│   ├── datetime_tool.py            # 日期时间工具
│   └── example_tools.py            # 其他示例工具
├── community/                   # 社区工具
│   ├── wikipedia_search.py         # Wikipedia搜索
│   ├── web_search.py               # 网络搜索
│   └── (其他社区工具文件)
├── custom/                      # 自定义工具
│   ├── weather_query.py            # 天气查询工具
│   ├── file_operations.py          # 文件操作工具
│   └── example_custom_tool.py      # 其他自定义工具
├── mcp/                         # MCP工具
│   └── mcp_loader.py               # MCP工具加载器
├── tool_loader.py               # 工具加载器
└── tool_service.py              # 工具服务
```

## 🎯 工作原理

### 1. 统一工具流程
1. **工具定义**: 在对应文件夹中定义工具
2. **自动发现**: 系统自动扫描并加载工具
3. **双向转换**: 统一适配器自动生成LangChain和OpenWebUI格式
4. **无缝使用**: 在LangChain Agent和OpenWebUI中都可以使用

### 2. 工具类型

#### 🔨 内置工具 (`builtin/`)
- LangChain官方提供的工具
- 经过充分测试的稳定工具
- 每个文件包含一组相关工具

#### 🌐 社区工具 (`community/`)
- 来自LangChain社区的工具
- 第三方开发的工具
- 需要额外依赖的工具

#### ⚙️ 自定义工具 (`custom/`)
- 项目特定的工具
- 业务逻辑相关的工具
- 用户自定义的工具

#### 🔗 MCP工具 (`mcp/`)
- Model Context Protocol工具
- 支持外部服务集成
- 动态加载的工具

## 🛠️ 添加新工具

### 方式1: 统一工具适配器（推荐）

```python
# backend/tools/custom/my_new_tool.py
from backend.tools.adapters.universal_tool_adapter import universal_adapter

def my_function(input_text: str, count: int = 1) -> str:
    """我的自定义函数"""
    return f"处理 {count} 次: {input_text}"

# 注册为统一工具
universal_adapter.register_tool(
    name="my_tool",
    function=my_function,
    description="我的自定义工具，可以处理文本",
    parameters={
        "type": "object",
        "properties": {
            "input_text": {"type": "string", "description": "输入文本"},
            "count": {"type": "integer", "description": "处理次数", "default": 1}
        },
        "required": ["input_text"]
    }
)
```

### 方式2: 传统LangChain工具（自动转换）

```python
# backend/tools/custom/my_langchain_tool.py
from langchain_core.tools import tool

@tool
def my_langchain_tool(input_text: str) -> str:
    """我的LangChain工具"""
    return f"LangChain处理: {input_text}"
```

### 方式3: StructuredTool（自动转换）

```python
# backend/tools/custom/my_structured_tool.py
from langchain_core.tools import StructuredTool

def my_function(param1: str, param2: int) -> str:
    return f"结果: {param1} * {param2}"

my_structured_tool = StructuredTool.from_function(
    func=my_function,
    name="my_structured_tool",
    description="我的结构化工具"
)
```

## 🚀 工具导出和使用

### 导出到OpenWebUI
```bash
cd docker
python export_tools.py
```

### 在OpenWebUI中使用
1. 重启OpenWebUI服务
2. 在工具列表中查看导出的工具
3. 启用需要的工具
4. 在对话中自动调用工具

## 📋 最佳实践

### 1. 文件组织
- **一个文件一个工具**: 便于定位和维护
- **相关工具分组**: 可以将相关工具放在同一文件中
- **清晰命名**: 文件名应该反映工具功能

### 2. 工具设计
- **明确的描述**: 工具描述要清晰易懂
- **合理的参数**: 参数设计要简洁实用
- **错误处理**: 要有完善的错误处理机制
- **类型注解**: 使用Python类型注解

### 3. 测试验证
- **功能测试**: 确保工具功能正常
- **参数验证**: 测试各种参数组合
- **错误场景**: 测试异常情况处理

## 🔍 故障排除

### 工具未加载
1. 检查文件路径是否正确
2. 检查Python语法是否有错误
3. 查看日志中的错误信息
4. 确认依赖是否已安装

### 工具执行失败
1. 检查工具函数实现
2. 验证参数类型和格式
3. 查看工具执行日志
4. 测试工具的独立运行

### OpenWebUI中看不到工具
1. 确认工具已导出: `python export_tools.py`
2. 重启OpenWebUI服务
3. 检查工具挂载路径
4. 查看OpenWebUI日志

## 📊 监控和维护

### 工具使用统计
- 通过日志查看工具调用频率
- 监控工具执行成功率
- 分析工具性能表现

### 定期维护
- 更新工具依赖
- 优化工具性能
- 清理无用工具
- 更新工具文档

## 🔮 扩展功能

### 计划中的功能
- 工具版本管理
- 工具权限控制
- 工具使用分析
- 工具市场集成
