# LangChain Agent Project v0.01

## 📋 项目概述

这是一个基于LangChain 2025标准的智能Agent项目，实现了三层工具架构，支持21个工具，具备现代化前端界面和完整的开发者模式。

## 🎯 版本信息

- **版本号**: v0.01
- **发布日期**: 2025-06-30
- **状态**: 生产就绪
- **LangChain版本**: 2025标准
- **Python版本**: 3.8+

## 🏗️ 架构特色

### 三层工具架构
1. **🏠 内置工具（14个）** - LangChain官方工具
2. **🔧 自定义工具（6个）** - 用户编写工具
3. **🔗 MCP工具（1个）** - Model Context Protocol支持

### Agent类型
- **LangChain核心Agent** ⭐ 推荐
- **自适应Agent** 
- **LangChain原生Agent**

## 📊 测试状态

| 测试项目 | 状态 | 说明 |
|---------|------|------|
| LangChain核心Agent | ✅ | 21个工具正常加载 |
| 基础对话功能 | ✅ | 智能对话响应 |
| 计算器工具 | ✅ | 数学表达式计算 |
| 文件工具 | ✅ | 文件操作功能 |
| 流式输出 | ✅ | 实时数据传输 |
| 内存功能 | ⚠️ | 需要优化 |
| Agent类型切换 | ✅ | 3个Agent正常 |
| 工具修复测试 | ✅ | 4/4通过，100%成功率 |

## 🛠️ 工具清单

### 内置工具（14个）
- `calculator` - 数学计算器
- `list_files` - 文件列表
- `read_file` - 文件读取
- `get_file_info` - 文件信息
- `web_search` - 网络搜索
- `local_search` - 本地搜索
- `python_repl_tool` - Python解释器
- `safe_python_exec` - 安全Python执行
- `python_calculator` - Python计算器
- `safe_shell_exec` - 安全Shell命令
- `system_info` - 系统信息
- `sql_query` - SQL查询
- `list_tables` - 数据库表列表
- `describe_table` - 表结构描述

### 自定义工具（6个）
- `demo_custom_tool` - 演示自定义工具
- `weather_tool` - 天气查询工具
- `random_quote_tool` - 随机名言工具
- `text_analyzer_tool` - 文本分析工具
- `text_formatter_tool` - 文本格式化工具
- `text_search_replace_tool` - 文本搜索替换工具

### MCP工具（1个）
- `mcp_placeholder_tool` - MCP框架占位符

## 🚀 快速开始

### 1. 环境准备
```bash
# 创建conda环境
conda create -n langchain-agent-env python=3.12
conda activate langchain-agent-env

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动项目
```bash
# 启动前端界面
python frontend/gradio_app.py

# 或使用启动脚本
python start.py
```

### 3. 访问界面
打开浏览器访问：http://localhost:7860

## 📁 项目结构

```
├── backend/                 # 后端核心代码
│   ├── agents/             # Agent实现
│   │   ├── langchain_core_agent.py    # ⭐ 核心Agent
│   │   ├── adaptive_agent.py          # 自适应Agent
│   │   └── langchain_native_agent.py  # 原生Agent
│   ├── tools/              # 三层工具架构
│   │   ├── builtin/        # 🏠 内置工具
│   │   ├── custom/         # 🔧 自定义工具
│   │   └── mcp/            # 🔗 MCP工具
│   ├── memory/             # 内存管理
│   ├── base/               # 基础类
│   └── utils/              # 工具函数
├── frontend/               # 前端界面
│   └── gradio_app.py       # Gradio应用
├── tests/                  # 测试文件
├── README.md               # 项目文档
├── requirements.txt        # 依赖列表
├── .gitignore             # Git忽略文件
├── VERSION                # 版本号
├── CHANGELOG.md           # 更新日志
└── PROJECT_INFO.md        # 项目信息
```

## 🔧 开发指南

### 添加自定义工具
1. 在 `backend/tools/custom/` 创建工具文件
2. 使用 `@tool` 装饰器定义工具
3. 在 `langchain_core_agent.py` 中添加导入

### 工具示例
```python
from langchain_core.tools import tool

@tool
def my_custom_tool(input_text: str) -> str:
    """我的自定义工具"""
    return f"处理结果: {input_text}"
```

## 🎯 下一版本计划

- [ ] 优化内存功能
- [ ] 添加更多内置工具
- [ ] 完善MCP工具支持
- [ ] 增强错误处理
- [ ] 性能优化
- [ ] 添加更多Agent类型

## 📞 支持

如有问题或建议，请查看：
- README.md - 详细文档
- CHANGELOG.md - 更新历史
- 开发者模式 - 调试信息
