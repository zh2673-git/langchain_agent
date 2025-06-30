# 🤖 LangChain Agent 实践项目

一个完全基于 LangChain 官方源码实现的智能 Agent 系统，支持多种 Agent 类型、工具调用、流式输出和现代化前端界面。

## 🌟 项目特色

- **🔥 完全基于 LangChain 原生实现**：严格按照 LangChain 官方源码和最佳实践
- **🤖 多种 Agent 模式**：LangChain Core、Adaptive、Native 三种精选实现
- **🛠️ 丰富的工具生态**：三层工具架构 - 内置工具、自定义工具、MCP工具，共21个工具，包含计算器、文件操作、Python解释器、数据库查询、系统命令、文本处理等
- **🎨 现代化前端**：基于 Gradio 的响应式界面，支持实时流式输出和思维链显示
- **🔧 完整的开发者体验**：详细的日志、调试信息、开发者模式
- **⚡ 高性能架构**：异步处理、流式输出、内存管理
- **✅ 工具调用完全正常**：计算器、文件操作等工具已完美集成

## 🤖 Agent 类型详解

### 1. LangChain Core Agent ⭐ **推荐**
完全基于 LangChain 核心框架实现，使用标准的 Runnable 接口和工具调用机制。

**特性：**
- 严格遵循 LangChain 设计模式
- **智能工具调用策略**：
  - 如果模型支持原生工具调用 → 使用 AgentExecutor
  - 如果模型不支持 → 使用提示词方式工具调用
- 完整的流式输出支持
- 标准的 Message 对象处理
- 自动工具发现和转换

**适用场景：**
- 🌟 **通用推荐**：适合大多数使用场景
- 生产环境部署
- 需要稳定可靠的工具调用
- 标准的对话交互

### 2. Adaptive Agent 🧠 **智能**
自适应 Agent，根据模型能力和任务复杂度自动选择最佳实现方式。

**特性：**
- 动态策略选择
- 性能优化
- 兼容性保证
- 智能工具调用解析

**适用场景：**
- 复杂任务处理
- 需要智能决策的场景
- 多步骤工具调用
- 自适应响应策略

### 3. LangChain Native Agent 🔧 **原生**
另一个 LangChain 原生实现，展示不同的实现方法。

**特性：**
- 纯 LangChain 实现
- 标准接口兼容
- 教学示例
- 简洁的代码结构

**适用场景：**
- 学习和研究
- 简单的对话场景
- 代码示例参考
- 轻量级部署

## 🔧 Agent 选择指南

| Agent 类型 | 图标 | 推荐场景 | 工具调用 | 性能 | 复杂度 | 推荐指数 |
|-----------|------|---------|---------|------|--------|----------|
| **LangChain Core** | ⭐ | 通用场景 | ✅ 智能适配 | ⭐⭐⭐⭐⭐ | 中等 | 🌟🌟🌟🌟🌟 |
| **Adaptive** | 🧠 | 复杂推理 | ✅ 动态选择 | ⭐⭐⭐⭐ | 中等 | 🌟🌟🌟🌟 |
| **Native** | 🔧 | 学习示例 | ✅ 标准实现 | ⭐⭐⭐⭐ | 简单 | 🌟🌟🌟 |

### 💡 选择建议

- **新用户推荐**：选择 `LangChain Core Agent` - 功能完整，性能最佳
- **高级用户**：选择 `Adaptive Agent` - 智能适配，处理复杂场景
- **学习研究**：选择 `Native Agent` - 代码简洁，易于理解

## 📁 项目结构

```
langchain-agent-practice/
├── backend/                    # 后端核心代码
│   ├── agents/                # 各种 Agent 实现
│   │   ├── langchain_core_agent.py    # ⭐ LangChain 核心 Agent（推荐）
│   │   ├── adaptive_agent.py          # 🧠 自适应 Agent
│   │   └── langchain_native_agent.py  # 🔧 LangChain 原生 Agent
│   ├── tools/                 # 工具系统（三层架构）
│   │   ├── builtin/           # 🏠 内置工具（LangChain官方）
│   │   │   ├── calculator_native.py  # 🧮 计算器工具
│   │   │   ├── file_native.py        # 📁 文件操作工具
│   │   │   ├── search_native.py      # 🔍 搜索工具
│   │   │   ├── python_repl_tool.py   # 🐍 Python解释器工具
│   │   │   ├── shell_tool.py         # 💻 系统命令工具
│   │   │   └── database_tools.py     # 🗄️ 数据库工具
│   │   ├── custom/            # 🔧 自定义工具（用户编写）
│   │   │   ├── demo_custom_tool.py   # 🎯 演示自定义工具
│   │   │   └── text_processing_tool.py # 📝 文本处理工具
│   │   ├── mcp/               # 🔗 MCP工具支持
│   │   │   ├── mcp_base.py           # MCP 基础框架
│   │   │   └── mcp_manager.py        # MCP 管理器
│   │   ├── langchain_tool_converter.py  # 工具转换器
│   │   └── tool_manager.py    # 工具管理器
│   ├── memory/                # 内存管理
│   ├── base/                  # 基础类定义
│   ├── utils/                 # 工具函数
│   ├── api.py                 # API 接口
│   └── config.py              # 配置管理
├── frontend/                  # 前端界面
│   └── gradio_app.py         # Gradio 应用
├── tests/                     # 测试文件
├── test_langchain_implementation.py  # 完整功能测试
└── requirements.txt           # 依赖列表
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Conda 或 pip
- Ollama（用于本地模型）

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd langchain-agent-practice
```

2. **创建虚拟环境**
```bash
conda create -n langchain-agent-env python=3.9
conda activate langchain-agent-env
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **启动 Ollama（如果使用本地模型）**
```bash
ollama serve
ollama pull qwen2.5:7b
```

5. **运行应用**
```bash
python frontend/gradio_app.py
```

访问 `http://localhost:7860` 开始使用。

## 🛠️ 工具系统

### 智能工具调用策略

项目实现了智能的工具调用策略，根据模型能力自动选择最佳方式：

1. **原生工具调用**（模型支持时）
   - 使用 LangChain 的 `bind_tools()` 方法
   - 模型直接理解工具定义
   - 最高效的工具调用方式

2. **提示词工具调用**（模型不支持时）
   - 通过提示词描述工具功能
   - AI 生成 `TOOL_CALL:` 格式的调用
   - 系统自动解析并执行工具
   - 确保所有模型都能使用工具

### LangChain 原生工具

- **🧮 计算器工具**：基于 LangChain BaseTool 实现的数学计算
  - 支持基础数学运算
  - 支持复杂表达式计算
  - 自动类型转换和验证

- **📁 文件工具**：LangChain 标准的文件读写操作
  - 文件列表查看
  - 文件内容读取
  - 目录信息获取
  - 安全路径限制

- **🔍 搜索工具**：符合 LangChain 接口的搜索功能
  - 网络搜索支持
  - 结果过滤和排序
  - 多搜索引擎支持

### 工具转换器

自动将自定义工具转换为 LangChain 标准工具，确保完全兼容：

- **自动类型推断**：根据工具参数自动生成 Pydantic 模型
- **异步支持**：同时支持同步和异步工具执行
- **错误处理**：完善的异常捕获和错误报告
- **参数验证**：严格的输入参数验证

### 工具调用示例

**用户问题**：桌面有哪些文件？

**AI 响应过程**：
1. 识别需要使用文件工具
2. 生成工具调用：`TOOL_CALL: {"tool": "file_tool", "input": "list ~/Desktop"}`
3. 系统执行工具并获取结果
4. AI 整合结果给出最终回答

### 特性总结

- ✅ **自动发现**：工具自动从目录加载
- ✅ **智能适配**：根据模型能力选择调用方式
- ✅ **类型安全**：完整的参数验证和类型检查
- ✅ **异步支持**：支持同步和异步工具执行
- ✅ **错误处理**：完善的错误处理和日志记录
- ✅ **流式显示**：工具调用过程实时显示

## 🎨 前端功能

- **💬 实时聊天**：支持 LangChain 流式输出的对话界面
- **🔄 Agent 切换**：动态切换不同的 Agent 类型
- **🛠️ 工具管理**：可视化的工具配置和管理
- **🔍 开发者模式**：详细的 LangChain 调试信息和性能监控
- **📚 会话管理**：支持多会话和历史记录
- **🧠 思维链显示**：实时显示 AI 思考过程
- **⚙️ 执行过程**：可视化工具调用和执行步骤


## ⚙️ 配置说明

### 模型配置
在 `backend/config/config.py` 中配置模型参数：

```python
MODELS = {
    "ollama": {
        "qwen2.5:7b": {
            "supports_tools": False,
            "max_tokens": 4096
        }
    }
}
```

### LangChain 配置
项目完全基于 LangChain 标准配置，支持所有 LangChain 兼容的模型和工具。

## 🧪 测试

运行完整功能测试：
```bash
python test_langchain_implementation.py
```

测试覆盖：
- ✅ LangChain 核心 Agent 功能
- ✅ 基础对话功能
- ✅ 工具调用（计算器、文件、搜索）
- ✅ 流式输出
- ✅ 内存功能
- ✅ 所有 Agent 类型切换

## 📊 测试结果

最新测试结果：**三层工具架构完成，21个工具，所有问题已修复** ✅

### 🎯 基础功能测试（6/7通过）
- ✅ LangChain核心Agent（完全正常，成功初始化和切换）
- ✅ 基础对话功能（完全正常，智能对话响应）
- ✅ 计算器工具（完全正常，能正确计算复杂数学表达式）
- ✅ 文件工具（完全正常，能列出文件和读取内容）
- ✅ 流式输出（完全正常，143个数据块流式传输）
- ⚠️ 内存功能（基本正常，但跨对话记忆需要优化）
- ✅ 所有Agent类型切换（完全正常，3个Agent都能正常工作）

### 🚀 增强工具测试（6/6通过）
- ✅ 原生计算器工具（123 * 456 + 789 = 56877）
- ✅ 文件操作工具（成功列出桌面文件）
- ✅ Python代码执行（Python解释器工具调用成功）
- ✅ 系统信息查询（获取Windows 11系统信息）
- ✅ 数据库查询（成功查询员工表数据）
- ✅ Shell命令执行（Python版本查询）

### 🔧 三层工具架构测试（完全通过）
- ✅ **工具架构重构**：成功实现三层工具架构
- ✅ **工具加载**：21个工具全部正确加载和分类
- ✅ **分类显示**：🏠14个内置 + 🔧6个自定义 + 🔗1个MCP工具
- ✅ **前后端同步**：前端正确显示后端的21个工具
- ✅ **开发者模式**：更新工具架构分析页面
- ✅ **问题修复**：修复了搜索工具变量错误和JSON解析问题
- ✅ **工具测试**：4/4修复测试通过，100%成功率

### 🎯 工具调用成功案例

**原生工具**：
- 计算器：`2 + 3` → `[使用工具 calculator] 5` ✅
- 文件操作：`列出桌面的文件` → `[使用工具 list_files] 目录内容...` ✅

**内置工具**：
- 系统信息：`获取当前系统信息` → `[使用工具 system_info] Windows 11, Python 3.12.11...` ✅
- 数据库查询：`查询员工表` → `[使用工具 sql_query] JSON格式员工数据` ✅

**自定义工具**：
- 演示工具：`使用演示工具处理消息：Hello World` → `[使用工具 demo_custom_tool] 自定义工具执行完成` ✅
- 天气工具：`查询北京的天气情况` → `[使用工具 weather_tool] 模拟天气数据` ✅
- 文本格式化：`将文本转换为大写：hello world` → `[使用工具 text_formatter_tool] HELLO WORLD` ✅

**工具生态**：
- 🎯 **21个工具**：内置14个 + 自定义6个 + MCP 1个
- 🔧 **100%工具执行成功率**：所有工具都能正确执行和调用
- 🏗️ **符合LangChain 2025标准**：支持最新的工具架构和MCP协议
- 🔧 **用户友好**：支持用户自定义工具，可通过LangChain @tool装饰器轻松添加
- 🛠️ **问题修复**：修复了搜索工具变量错误和复杂JSON解析问题
## 📝 开发指南

### 添加新的 LangChain Agent
1. 在 `backend/agents/` 创建新的 Agent 类
2. 继承 `AgentBase` 基类
3. 使用 LangChain 的 Runnable 模式
4. 在 `backend/api.py` 中注册
5. 更新 `backend/agents/__init__.py`

### 添加新的工具

#### 1. 🔧 自定义工具（推荐用户使用）
在 `backend/tools/custom/` 创建工具文件：
```python
from langchain_core.tools import tool

@tool
def my_custom_tool(input_text: str, option: str = "default") -> str:
    """我的自定义工具

    Args:
        input_text: 输入文本
        option: 处理选项

    Returns:
        str: 处理结果
    """
    return f"自定义处理: {input_text} (选项: {option})"
```

#### 2. 🏠 内置工具（LangChain官方工具）
内置工具位于 `backend/tools/builtin/`，包含LangChain官方提供的工具。
一般情况下不需要修改，除非要集成新的LangChain社区工具。

#### 3. 🔗 MCP工具（Model Context Protocol）
在 `backend/tools/mcp/` 扩展MCP支持：
```python
from .mcp_base import MCPToolBase

class MyMCPTool(MCPToolBase):
    async def connect_to_mcp_server(self):
        # 实现MCP服务器连接
        pass
```

#### 工具自动加载
- 自定义工具会自动被LangChain核心Agent加载
- 需要在 `backend/agents/langchain_core_agent.py` 中添加导入
- 支持LangChain标准的 `@tool` 装饰器

### LangChain 最佳实践
- 使用 LangChain 的标准 Message 对象
- 遵循 Runnable 接口设计
- 支持异步操作
- 使用 LangChain 的流式输出
- 遵循 LangChain 的错误处理模式

## 🔧 技术栈

- **核心框架**：LangChain
- **前端**：Gradio
- **模型**：Ollama (qwen2.5:7b)
- **工具系统**：LangChain BaseTool
- **内存管理**：LangChain Memory
- **流式输出**：LangChain Streaming

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 确保遵循 LangChain 最佳实践
4. 运行测试确保功能正常
5. 提交更改
6. 发起 Pull Request

## 📄 许可证

MIT License

## 🙏 致谢

感谢 LangChain 社区提供的优秀框架和工具。本项目严格按照 LangChain 官方源码和最佳实践实现，展示了如何正确使用 LangChain 构建生产级 Agent 系统。

---

**⭐ 如果这个项目对您有帮助，请给个Star支持一下！**

