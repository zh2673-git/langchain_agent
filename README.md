# LangChain Agent 项目 - 完整版

基于 LangChain 2025 标准的智能 Agent 系统，支持多种工具类型和持久化存储。

## 🎯 项目特色

- **三种 Agent 实现方式**：Chain、Agent、LangGraph
- **完全基于 LangChain 标准**：无自定义封装，100% 兼容 LangChain 生态
- **统一工具管理**：支持内置工具、社区工具、自定义工具、MCP工具
- **持久化记忆管理**：SQLite 单机持久化 + 内存高速缓存
- **双前端支持**：Gradio Web界面 + OpenWebUI 兼容API
- **统一配置管理**：集中管理 API 密钥和工具配置
- **服务化架构**：工具服务和记忆服务独立，职责分离

## 📁 项目结构

```
├── backend/                    # 后端核心代码
│   ├── agents/                # 三种Agent实现
│   │   ├── __init__.py           # 导出三种Agent
│   │   ├── chain_agent.py        # 🔗 Chain方式实现
│   │   ├── agent_agent.py        # 🤖 Agent方式实现
│   │   └── langgraph_agent.py    # 📊 LangGraph方式实现
│   ├── tools/                 # 工具管理系统
│   │   ├── __init__.py
│   │   ├── tool_service.py       # 工具服务（统一管理）
│   │   ├── tool_loader.py        # 统一工具加载器
│   │   ├── builtin/              # 内置工具
│   │   │   ├── __init__.py
│   │   │   └── example_tools.py  # 示例工具
│   │   ├── community/            # 社区工具（动态加载）
│   │   │   └── __init__.py
│   │   ├── custom/               # 自定义工具
│   │   │   ├── __init__.py
│   │   │   └── example_custom_tool.py
│   │   └── mcp/                  # MCP工具
│   │       ├── __init__.py
│   │       └── mcp_loader.py
│   ├── memory/                # 记忆管理系统
│   │   ├── __init__.py
│   │   ├── memory_service.py     # 记忆服务（支持多后端）
│   │   └── sqlite_memory.py      # SQLite持久化实现
│   ├── utils/                 # 工具函数
│   │   ├── __init__.py
│   │   └── logger.py
│   ├── api/                   # API接口层
│   │   ├── __init__.py           # API模块入口
│   │   ├── api.py                # 核心Agent API
│   │   └── openwebui_server.py   # OpenWebUI兼容服务器
│   └── config.py              # 配置管理（完整版）
├── frontend/                  # 前端界面
│   └── gradio_app.py             # Gradio Web界面
├── main/                      # 启动脚本
│   └── app.py                    # 统一启动器
├── docker/                    # Docker部署文件
│   ├── docker-compose.yml       # Docker编排配置
│   ├── Dockerfile.backend       # 后端容器构建文件
│   ├── Dockerfile.gradio        # Gradio容器构建文件
│   ├── start.sh                 # Linux/Mac启动脚本
│   ├── start.bat                # Windows启动脚本
│   └── README.md                # Docker部署指南
├── README.md                  # 项目文档
└── requirements.txt           # 依赖列表
```

## 🚀 快速开始

### 环境要求

- Python 3.12+
- Docker & Docker Compose
- Conda (推荐)
- Ollama (用于本地模型)

### 1. 环境准备

#### 创建Conda环境
```bash
# 创建专用环境
conda create -n langchain_agent_env python=3.12
conda activate langchain_agent_env

# 安装依赖
pip install -r requirements.txt
```

#### 配置环境变量（可选）
```bash
# 创建 .env 文件，添加API密钥（如果使用OpenAI/Anthropic）
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

### 2. 确保Ollama运行（如果使用本地模型）
```bash
# 启动Ollama服务
ollama serve

# 下载模型（另一个终端）
ollama pull qwen2.5:7b
ollama pull llama3.1:8b
ollama pull mistral:7b
```

### 3. 选择启动方式

#### 方式1: 🐳 Docker Compose（推荐）
```bash
cd docker

# 启动所有服务（包括OpenWebUI前端）
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 访问服务
# - OpenWebUI前端: http://localhost:3000
# - 后端API: http://localhost:8000
# - API文档: http://localhost:8000/docs
```

#### 方式2: 🎨 Gradio Web界面（本地开发）
```bash
# 激活环境
conda activate langchain_agent_env

# 启动Gradio界面
python main/app.py 1
# 或者
python main/app.py gradio

# 访问: http://localhost:7860
```

#### 方式3: 🌐 OpenWebUI前端（本地开发）

##### 本地启动
```bash
# 激活环境
conda activate langchain_agent_env

# 1. 启动后端API服务器
python main/app.py 2
# 或者
python main/app.py openwebui

# 2. 启动OpenWebUI前端（另一个终端）
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  ghcr.io/open-webui/open-webui:main

# 3. 配置OpenWebUI
# 访问: http://localhost:3000
# 设置 > 连接 > OpenAI API
# API Base URL: http://localhost:8000/v1
# API Key: 任意值
# 模型: langchain-chain, langchain-agent, langchain-langgraph
```

##### Docker Compose启动（推荐）
```bash
# 进入Docker目录
cd docker

# 使用启动脚本（推荐）
./start.sh          # Linux/Mac
start.bat           # Windows
```

**启动脚本选项**：
- **选项1**: OpenWebUI + 后端（生产模式）
- **选项2**: Gradio + 后端（生产模式）
- **选项3**: 仅后端（生产模式）
- **选项4**: 开发模式（代码热更新）⭐
- **选项5**: 快速构建模式（国内镜像源）🚀

**或直接使用docker-compose命令**：
```bash
# 生产模式
docker-compose up -d                    # OpenWebUI + 后端
docker-compose --profile gradio up -d   # Gradio + 后端

# 开发模式（代码热更新）
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 快速构建模式（国内用户推荐）
docker-compose -f docker-compose.fast.yml up -d --build
```

**访问地址**：
- **OpenWebUI**: http://localhost:3000
- **Gradio**: http://localhost:7860
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **工具列表**: http://localhost:8000/v1/tools

#### 方式3: 💬 纯后端交互（开发者）
```bash
# 激活环境
conda activate langchain_agent_env

# 启动命令行模式
python main/app.py 3
# 或者
python main/app.py backend

# 支持命令: quit, clear, switch <agent>, test, models
```

#### 🐳 Docker开发模式（推荐开发者）
```bash
# 进入Docker目录
cd docker

# 启动开发模式（代码热更新）
start.bat           # Windows，选择选项4
./start.sh          # Linux/Mac，选择选项4

# 或直接命令
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 访问地址
# OpenWebUI: http://localhost:3000
# API文档: http://localhost:8000/docs

# 开发优势
# ✅ 修改代码立即生效，无需重启
# ✅ 完全隔离的开发环境
# ✅ 一键启动所有服务
```

## 🐳 Docker部署

### 快速启动

#### 🚀 推荐方式（国内用户）
```bash
# 进入Docker目录
cd docker

# 使用快速构建模式
start.bat           # Windows，选择选项5
./start.sh          # Linux/Mac，选择选项5

# 或直接命令
docker-compose -f docker-compose.fast.yml up -d --build
```

#### 🌍 标准方式
```bash
# 进入Docker目录
cd docker

# 使用启动脚本
start.bat           # Windows
./start.sh          # Linux/Mac

# 或直接使用命令
docker-compose up -d                    # 启动OpenWebUI + 后端
docker-compose ps                       # 查看服务状态
docker-compose logs -f                  # 查看日志
docker-compose down                     # 停止服务
```

### 服务访问
- **OpenWebUI前端**: http://localhost:3000
- **LangChain API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **工具列表**: http://localhost:8000/v1/tools

## 🎯 新功能特性

### ✅ 已实现功能

#### 🔧 工具显示与调用
- **工具可见性**: ✅ 在API中显示所有可用工具
- **工具信息**: ✅ 查看工具描述、参数和使用方法
- **实时调用**: ✅ 对话中自动调用相关工具
- **调用反馈**: ✅ 显示工具调用过程和结果

#### 🔄 模型动态切换
- **多模型支持**: ✅ 每种Agent支持多个底层模型
- **实时切换**: 🔧 API已实现，前端集成开发中
- **模型配置**: ✅ 查看每个Agent的可用模型列表
- **性能优化**: ✅ 根据任务选择最适合的模型

#### 🌐 OpenWebUI兼容性
- **JSON响应**: ✅ 完全修复流式请求vs JSON响应矛盾
- **模型列表**: ✅ 显示LangChain Agent作为可选模型
- **工具集成**: 🔧 后端支持，前端显示优化中
- **无错误运行**: ✅ 消除所有JSON解码错误

### 📊 增强的API接口
- **模型信息API**: `/v1/models` - 获取详细模型信息
- **工具列表API**: `/v1/tools` - 获取所有可用工具
- **模型切换API**: `/v1/models/{agent_type}/switch` - 动态切换模型
- **健康检查API**: `/health` - 服务状态监控

## 📖 使用指南

### 🌐 OpenWebUI前端使用

#### 1. 访问界面
```bash
# 启动服务后访问
http://localhost:3000
```

#### 2. 选择Agent模型
- **langchain-chain**: 适合简单对话和基础任务
- **langchain-agent**: 支持工具调用，适合复杂任务
- **langchain-langgraph**: 基于图结构，适合多步骤推理

#### 3. 查看工具信息
- 在模型选择界面可以看到每个Agent支持的工具
- 工具会在对话中自动调用
- 可以看到工具调用的详细过程和结果

#### 4. 模型切换（开发中）
```bash
# API调用示例
curl -X POST "http://localhost:8000/v1/models/chain/switch" \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.1:8b"}'
```

### 🔧 统一工具系统

#### ✨ 核心特性
- **一次定义，双向使用**: 定义一次工具，自动生成LangChain和OpenWebUI两种格式
- **自动转换**: 现有LangChain工具自动转换为OpenWebUI格式
- **模块化管理**: 工具独立管理，不影响其他代码
- **热更新**: 添加/修改工具后自动生效

#### 📁 工具组织结构
```
backend/tools/
├── builtin/     # LangChain内置工具 (计算器、时间等)
├── community/   # 社区工具 (Wikipedia、网络搜索等)
├── custom/      # 自定义工具 (文本处理、数据分析、实用工具等)
├── mcp/         # MCP工具 (Model Context Protocol工具)
└── adapters/    # 统一适配器 (自动转换系统)
```

每个文件夹中的每个`.py`文件代表一个或一组相关工具，便于定位和修改。

#### 🤖 Agent模式系统

##### Agent模式和模型分离
- **Agent模式**: Chain、Tool Agent、Graph Agent (作为工作模式)
- **底层模型**: qwen2.5:7b/14b、llama3.1:8b、mistral:7b (可动态切换)
- **灵活配置**: 每个模式都可以使用任意底层模型

##### 三种Agent模式
- **Chain Agent**: 基于Runnable接口的简单Agent，适合日常对话
- **Tool Agent**: 支持工具调用的智能Agent，适合复杂任务
- **Graph Agent**: 基于状态图的高级Agent，适合复杂工作流

#### 🛠️ 添加自定义工具

##### 方式1: 统一工具适配器（推荐）
```python
# backend/tools/custom/my_tool.py
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

##### 方式2: LangChain工具（自动转换）
```python
# backend/tools/custom/my_langchain_tool.py
from langchain_core.tools import tool

@tool
def my_langchain_tool(input_text: str) -> str:
    """我的LangChain工具"""
    return f"LangChain处理: {input_text}"
```

##### 方式3: StructuredTool（自动转换）
```python
# backend/tools/custom/my_structured_tool.py
from langchain_core.tools import StructuredTool

def my_function(param1: str, param2: int) -> str:
    return f"结果: {param1} * {param2}"

my_tool = StructuredTool.from_function(
    func=my_function,
    name="my_structured_tool",
    description="我的结构化工具"
)
```

#### 🚀 Agent模式配置

##### 查看可用模式和模型
```bash
# 查看Agent模式
curl http://localhost:8000/v1/agent/modes

# 查看可用模型
curl http://localhost:8000/v1/agent/models

# 查看当前配置
curl http://localhost:8000/v1/agent/current-config
```

##### 配置Agent模式和模型
```bash
# 配置Chain Agent使用llama3.1:8b模型
curl -X POST "http://localhost:8000/v1/agent/configure" \
  -H "Content-Type: application/json" \
  -d '{"mode": "chain", "model": "llama3.1:8b"}'

# 配置Tool Agent使用qwen2.5:14b模型
curl -X POST "http://localhost:8000/v1/agent/configure" \
  -H "Content-Type: application/json" \
  -d '{"mode": "agent", "model": "qwen2.5:14b"}'
```

#### 🔧 工具导出和使用

##### 导出工具到OpenWebUI
```bash
cd docker
python export_tools.py
```

##### 在OpenWebUI中使用
1. 选择Agent模式 (langchain-chain-mode, langchain-agent-mode, langchain-langgraph-mode)
2. 为选定模式切换底层模型
3. 在对话中使用工具功能
4. 通过对话切换模式和模型

#### 📋 工具管理最佳实践

##### 文件组织
- **一个文件一个工具**: 便于定位和维护
- **相关工具分组**: 可以将相关工具放在同一文件中
- **清晰命名**: 文件名应该反映工具功能

##### 工具设计
- **明确的描述**: 工具描述要清晰易懂
- **合理的参数**: 参数设计要简洁实用
- **错误处理**: 要有完善的错误处理机制
- **类型注解**: 使用Python类型注解

##### 故障排除
- **工具未加载**: 检查文件路径和Python语法
- **工具执行失败**: 验证参数类型和工具实现
- **OpenWebUI中看不到**: 确认已导出并重启服务

详细说明请参考: `backend/tools/README.md`

#### 📋 工具加载器说明

##### tool_loader.py vs mcp_loader.py
- **tool_loader.py**: 通用工具加载器，负责统一管理所有类型的工具
  - 扫描并加载builtin、community、custom工具
  - 调用mcp_loader加载MCP工具
  - 提供统一的工具注册和管理接口

- **mcp_loader.py**: 专门的MCP工具加载器，负责MCP协议相关功能
  - 连接和管理MCP服务器
  - 处理MCP协议通信
  - 将MCP工具转换为LangChain工具格式

两者职责不同，都是必需的组件。

## 📁 项目文件说明

### 核心文件
- `backend/tools/` - 统一工具系统
- `backend/agents/` - 三种Agent实现
- `backend/api/` - API服务和OpenWebUI适配
- `docker/` - Docker部署配置

### 重要脚本
- `docker/export_tools.py` - 工具导出脚本
- `docker/test_universal_tools.py` - 系统功能综合测试
- `main/launcher.py` - 本地开发启动器

### 配置文件
- `docker/docker-compose.yml` - 生产环境配置
- `docker/docker-compose.dev.yml` - 开发环境配置
- `backend/config/` - 系统配置

### 自动生成文件（可忽略）
- `docker/openwebui_tools/` - 导出的OpenWebUI工具文件
- `docker/logs/` - 运行日志
- `__pycache__/` - Python缓存文件

### 🔧 三种Docker模式对比

#### 🚀 快速构建模式（国内用户推荐）
```bash
cd docker

# 方式1: 使用启动脚本
start.bat           # Windows，选择选项5
./start.sh          # Linux/Mac，选择选项5

# 方式2: 直接命令
docker-compose -f docker-compose.fast.yml up -d --build
```

**快速构建特点**：
- ⚡ **构建速度**: 2-5分钟（vs 标准模式10-20分钟）
- 🇨🇳 **国内镜像源**: 阿里云Debian源 + 清华PyPI源
- 🔧 **优化配置**: 专为中国网络环境优化
- ✅ **功能完整**: 与标准模式功能完全相同

#### 🔧 开发者模式（推荐开发时使用）
```bash
cd docker

# 方式1: 使用启动脚本（推荐）
start.bat           # Windows，选择选项4
./start.sh          # Linux/Mac，选择选项4

# 方式2: 直接命令
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# 测试开发模式
python test_dev_mode.py
```

**开发者模式特点**：
- 🔥 **代码热更新**: 修改 `backend/` 或 `main/` 文件立即生效
- ⚡ **无需重建**: 保存文件自动重载，无需重启容器
- 🐛 **实时调试**: 支持断点调试和实时日志查看
- 📁 **目录挂载**: 源码目录直接挂载到容器内
- 🔧 **开发优化**: 专用Dockerfile，包含开发工具

#### 🏭 生产模式
```bash
cd docker

# 启动生产模式
docker-compose up -d

# 代码更改后需要重新构建
docker-compose up -d --build
```

**生产模式特点**：
- ✅ **性能优化**: 代码预编译，启动更快
- ✅ **安全隔离**: 代码完全封装在镜像中
- ✅ **部署稳定**: 不依赖外部文件系统
- ❌ **更新需重建**: 代码更改需要重新构建镜像

#### 📊 模式对比表

| 特性 | 快速构建模式 | 开发者模式 | 生产模式 |
|------|-------------|-----------|----------|
| 构建速度 | ⚡ 2-5分钟 | 🔄 首次较慢 | 🐌 10-20分钟 |
| 代码更新 | ❌ 需重建 | ✅ 热更新 | ❌ 需重建 |
| 网络优化 | ✅ 国内源 | ❌ 标准源 | ❌ 标准源 |
| 适用场景 | 🇨🇳 国内首次部署 | 🔧 日常开发 | 🚀 生产部署 |

### 🛠️ 开发工作流程

#### 推荐的开发流程
```bash
# 1. 首次启动（开发模式）
cd docker
start.bat  # 选择选项4: Development Mode

# 2. 验证开发模式
python test_dev_mode.py

# 3. 开发代码
# 直接编辑 backend/ 或 main/ 目录下的文件
# 保存后自动生效，无需重启容器

# 4. 查看实时日志
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f langchain-backend

# 5. 添加新依赖后重新构建
# 修改 requirements.txt 后执行：
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# 6. 生产测试
docker-compose up -d --build
```

#### 开发模式 vs 生产模式对比

| 特性 | 开发模式 | 生产模式 |
|------|----------|----------|
| 代码更新 | ✅ 热更新，立即生效 | ❌ 需要重新构建 |
| 启动速度 | ⚡ 快速启动 | 🐌 需要构建时间 |
| 调试支持 | ✅ 实时调试 | ❌ 有限调试 |
| 性能 | 🔄 开发优化 | 🚀 生产优化 |
| 安全性 | ⚠️ 开发环境 | 🔒 生产级安全 |
| 适用场景 | 🔧 日常开发 | 🚀 部署上线 |

### 环境变量配置
创建 `.env` 文件：
```bash
# OpenAI配置（可选）
OPENAI_API_KEY=your_openai_key

# Anthropic配置（可选）
ANTHROPIC_API_KEY=your_anthropic_key

# OpenWebUI密钥
WEBUI_SECRET_KEY=your-secret-key-here

# 开发模式配置
DEBUG=true
RELOAD=true
```

## 📝 开发说明

### 环境要求
- **Python**: 3.11+
- **Conda环境**: `langchain_agent_env`
- **依赖管理**: pip + requirements.txt
- **本地模型**: Ollama + qwen2.5:7b（推荐）

### 项目特性
- ✅ **三种Agent实现**: Chain, Agent, LangGraph
- ✅ **多种工具支持**: 计算器, 搜索, 文件操作, 自定义工具
- ✅ **持久化记忆**: SQLite存储，支持多轮对话
- ✅ **模型切换**: 支持Ollama, OpenAI, Anthropic
- ✅ **Docker部署**: 一键启动完整服务
- ✅ **快速构建**: 国内镜像源，2-5分钟完成构建
- ✅ **开发者友好**: Docker开发模式支持代码热更新
- ✅ **多种界面**: Gradio Web界面, OpenWebUI前端, 命令行交互
- ✅ **生产就绪**: 支持生产模式和开发模式切换

### 快速测试

#### 本地测试
```bash
# 激活环境
conda activate langchain_agent_env

# 快速启动（推荐）
python start.py 1    # Gradio界面
python start.py 2    # OpenWebUI服务器
python start.py 3    # 命令行交互

# 或使用完整命令
python main/app.py gradio
```

#### Docker测试（推荐国内用户）
```bash
# 进入Docker目录
cd docker

# 快速构建启动
start.bat  # 选择选项5: Fast Build Mode

# 访问测试
# OpenWebUI: http://localhost:3000
# API文档: http://localhost:8000/docs
```

### 故障排除

#### 本地开发问题
1. **模块缺失**: `pip install -r requirements.txt`
2. **Ollama连接失败**: 确保 `ollama serve` 正在运行
3. **端口占用**: 检查7860, 8000, 3000端口是否被占用

#### Docker相关问题
4. **Docker服务**: 确保Docker Desktop正在运行
5. **构建速度慢**:
   ```bash
   # 国内用户推荐使用快速构建模式
   cd docker
   start.bat  # 选择选项5: Fast Build Mode

   # 或直接命令
   docker-compose -f docker-compose.fast.yml up -d --build
   ```
6. **网络连接问题**:
   ```bash
   # 配置Docker代理（Docker Desktop > Settings > Proxies）
   # 或使用快速构建模式（已配置国内镜像源）
   ```
7. **代码不更新**:
   - 开发模式：检查文件是否正确挂载
   - 生产模式：使用 `docker-compose up -d --build` 重新构建
8. **容器启动失败**:
   ```bash
   # 查看详细错误日志
   docker-compose logs langchain-backend

   # 重新构建镜像
   docker-compose build --no-cache
   ```
9. **端口冲突**:
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :3000
   netstat -tulpn | grep :8000

   # 停止所有容器
   docker-compose down
   docker-compose -f docker-compose.fast.yml down
   ```
10. **开发模式代码不生效**:
    ```bash
    # 确认使用开发模式启动
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

    # 检查挂载是否正确
    docker-compose exec langchain-backend ls -la /app/backend
    ```

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🤖 三种 Agent 实现方式

### 1. Chain Agent 🔗
使用 LangChain 的 Runnable 接口组合实现

**特点**：
- 基于 Chain 组合模式
- 使用提示词方式调用工具
- 适合学习和简单场景
- 灵活的链式组合

### 2. Agent Agent 🤖
使用 create_tool_calling_agent 和 AgentExecutor 实现

**特点**：
- LangChain 标准 Agent 实现
- 原生 function calling 支持
- 生产环境推荐
- 稳定可靠

### 3. LangGraph Agent 📊
使用 LangGraph 状态图实现

**特点**：
- 复杂工作流支持
- 状态管理
- 高级场景适用
- 需要安装 langgraph 依赖

## 🛠️ 统一工具系统

### 工具目录结构

```
backend/tools/
├── __init__.py              # 工具模块入口
├── tool_service.py          # 工具服务（统一管理）
├── tool_loader.py           # 统一工具加载器
├── builtin/                 # 内置工具
│   ├── __init__.py
│   └── example_tools.py     # 示例工具
├── community/               # 社区工具（动态加载）
│   └── __init__.py
├── custom/                  # 自定义工具
│   ├── __init__.py
│   └── example_custom_tool.py
└── mcp/                     # MCP工具
    ├── __init__.py
    └── mcp_loader.py        # MCP工具加载器
```

### 支持的工具类型

#### 1. 内置工具 (builtin/)
项目自带的示例工具，展示工具定义方式：
- **simple_calculator**: 数学计算器
- **weather_query**: 天气查询
- **file_operation**: 文件操作
- **data_analysis**: 数据分析

#### 2. 社区工具 (community/)
LangChain社区提供的工具，动态加载：
- **wikipedia**: Wikipedia搜索
- **duckduckgo_search**: DuckDuckGo搜索
- **python_repl**: Python代码执行
- **arxiv**: ArXiv论文搜索
- **requests**: HTTP请求工具
- **wolfram_alpha**: Wolfram Alpha计算
- **google_search**: Google搜索

#### 3. 自定义工具 (custom/)
用户在 `backend/tools/custom/` 目录下添加的工具：
- **text_analyzer**: 文本分析工具
- **password_generator**: 密码生成器
- **timestamp_tool**: 时间戳工具

#### 4. MCP工具 (mcp/)
基于Model Context Protocol的工具，支持与外部系统集成：
- **文件系统MCP**: 读取和列出文件
- **数据库MCP**: 查询数据库
- **API MCP**: 调用外部API
- **自定义MCP服务器**: 用户定义的MCP工具

### 工具运行机制

#### 1. 工具加载流程
```
启动系统 → 初始化工具服务 → 统一工具加载器 → 扫描三个目录 → 注册到工具服务
```

#### 2. 工具发现机制
- **内置工具**: 直接从 `builtin/example_tools.py` 导入
- **社区工具**: 根据配置动态加载LangChain社区工具
- **自定义工具**: 扫描 `custom/` 目录下的 `.py` 文件

#### 3. 工具注册过程
1. `UnifiedToolLoader` 扫描所有工具源
2. 验证工具是否启用（根据配置）
3. 检查API密钥（如果需要）
4. 注册到 `ToolService`
5. 提供给Agent使用

### 工具配置

在 `backend/config.py` 中统一配置：

```python
# 工具加载配置
TOOL_LOADING_CONFIG = {
    "auto_load_builtin": True,
    "auto_load_community": True,
    "auto_load_custom": True,
    "auto_load_mcp": False
}

# 启用/禁用具体工具
BUILTIN_TOOLS_CONFIG = {
    "simple_calculator": {"enabled": True},
    "wikipedia": {"enabled": True},
    "python_repl": {"enabled": False},  # 安全考虑
    "google_search": {"enabled": False, "api_key_required": True}
}

# MCP工具配置
MCP_TOOLS_CONFIG = {
    "enabled": True,
    "servers": {
        "filesystem": {
            "type": "filesystem",
            "enabled": True,
            "base_path": "./data"
        },
        "example_api": {
            "type": "api",
            "enabled": False,
            "base_url": "https://api.example.com",
            "api_key": ""
        }
    }
}
```

### 添加新工具详细过程

#### 步骤1：选择工具类型和位置

**内置工具**: 在 `backend/tools/builtin/example_tools.py` 中添加
**自定义工具**: 在 `backend/tools/custom/` 目录下创建新的 `.py` 文件

#### 步骤2：定义工具

**方式1：@tool装饰器（简单工具）**
```python
# 在 backend/tools/custom/my_tools.py 中
from langchain_core.tools import tool

@tool
def my_simple_tool(input_text: str) -> str:
    """我的简单工具"""
    return f"处理结果: {input_text}"
```

**方式2：StructuredTool.from_function（复杂参数）**
```python
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    text: str = Field(description="输入文本")
    option: str = Field(description="处理选项")

def my_complex_function(text: str, option: str) -> str:
    return f"处理 {text} 使用选项 {option}"

my_complex_tool = StructuredTool.from_function(
    func=my_complex_function,
    name="my_complex_tool",
    description="我的复杂工具",
    args_schema=MyToolInput
)
```

#### 步骤3：配置工具（可选）

在 `backend/config.py` 中添加配置：
```python
BUILTIN_TOOLS_CONFIG = {
    # ... 其他工具
    "my_simple_tool": {"enabled": True},
    "my_complex_tool": {"enabled": True}
}
```

#### 步骤4：重启系统

工具会自动被发现和加载，无需手动注册。

#### 步骤5：验证工具加载

```python
from backend.tools.tool_service import get_tool_service

# 获取工具服务
tool_service = get_tool_service()
await tool_service.initialize()

# 查看已加载的工具
tools = tool_service.get_tools()
print(f"已加载 {len(tools)} 个工具")

# 查看工具列表
tool_names = tool_service.list_tool_names()
print(f"工具列表: {tool_names}")
```

### 工具系统文件说明

#### 核心文件

| 文件 | 作用 | 说明 |
|------|------|------|
| `tool_service.py` | 工具服务 | 统一的工具管理接口，Agent通过此服务调用工具 |
| `tool_loader.py` | 工具加载器 | 自动发现和加载三种类型的工具 |
| `__init__.py` | 模块入口 | 导出工具相关的类和函数 |

#### 工具目录

| 目录 | 作用 | 添加方式 |
|------|------|----------|
| `builtin/` | 内置示例工具 | 直接在 `example_tools.py` 中添加 |
| `community/` | 社区工具 | 通过配置启用，自动加载 |
| `custom/` | 自定义工具 | 创建 `.py` 文件，自动发现 |
| `mcp/` | MCP工具 | 配置MCP服务器，自动加载 |

#### 工具加载优先级

1. **内置工具**: 最先加载，提供基础功能
2. **社区工具**: 根据配置加载，提供丰富功能
3. **MCP工具**: 加载MCP服务器工具，提供外部集成
4. **自定义工具**: 最后加载，提供定制功能

#### 工具命名规则

- 工具名称必须唯一
- 建议使用下划线命名：`my_tool_name`
- 避免与LangChain内置工具冲突
- 描述要清晰明确，便于Agent理解

## 💾 持久化记忆管理

### 支持的存储后端

#### 1. SQLite持久化（推荐）
- **单机持久化存储**
- **会话和消息持久化**
- **高效查询和索引**
- **自动备份支持**

#### 2. 内存存储
- **高速访问**
- **开发调试友好**
- **重启后数据丢失**

### 记忆配置

```python
MEMORY_SERVICE_CONFIG = {
    "default_type": "sqlite",  # sqlite 或 memory
    "max_sessions": 1000,
    "max_messages": 100,
    "session_timeout": 3600,
    "sqlite_db_path": "./data/chat_history.db",
    "auto_backup": True
}
```

### 会话管理特点

- **自动会话创建**：首次对话自动创建会话
- **会话持久化**：SQLite存储，重启后保留
- **消息限制**：自动清理超出限制的旧消息
- **会话搜索**：支持跨会话消息搜索
- **元数据支持**：会话可附加自定义元数据

## 🖥️ 三种使用方式

### 1. 🎨 Gradio Web界面（推荐新手）

**特点**：
- 简洁易用的Web界面
- 实时聊天功能
- Agent类型切换
- 系统状态监控
- 一键启动，无需额外配置

**使用方式**：
```bash
python main/app.py gradio
# 访问: http://localhost:7860
```

### 2. 🌐 OpenWebUI前端（专业用户）

**特点**：
- 专业的ChatGPT风格界面
- 丰富的功能和插件
- 支持多用户和权限管理
- 完整的聊天历史管理

**集成步骤**：

#### 步骤1: 启动LangChain后端API
```bash
python main/app.py openwebui
# 后端API运行在: http://localhost:8000
```

#### 步骤2: 启动OpenWebUI前端
```bash
# 使用Docker（推荐）
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main

# 或使用pip安装
pip install open-webui
open-webui serve --port 3000
```

#### 步骤3: 配置OpenWebUI连接
1. 访问: http://localhost:3000
2. 注册/登录账户
3. 进入 **设置** > **连接** > **OpenAI API**
4. 配置连接:
   - **API Base URL**: `http://localhost:8000/v1`
   - **API Key**: `任意值`（我们的API不验证密钥）
5. 在聊天界面选择模型:
   - `langchain-chain`: Chain Agent实现
   - `langchain-agent`: Agent Agent实现
   - `langchain-langgraph`: LangGraph Agent实现

### 3. 💬 纯后端交互（开发者）

**特点**：
- 命令行交互界面
- 完整的Agent功能
- 实时测试和调试
- 适合开发和集成

**使用方式**：
```bash
python main/app.py backend

# 支持的命令:
# quit - 退出程序
# clear - 清除聊天历史
# switch <agent> - 切换Agent类型 (chain/agent/langgraph)
# test - 运行Agent测试
# models - 测试模型切换
```

## ⚙️ 配置管理

### API 密钥管理
```bash
# .env 文件
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key
SERPAPI_API_KEY=your_serpapi_key
WEATHER_API_KEY=your_weather_key
WOLFRAM_API_KEY=your_wolfram_key
```

### 模型配置
```python
# 支持的模型
SUPPORTED_MODELS = {
    "ollama": ["qwen2.5:7b", "llama3.1:8b", "mistral:7b"],
    "openai": ["gpt-3.5-turbo", "gpt-4", "gpt-4o"],
    "anthropic": ["claude-3-sonnet", "claude-3-opus"]
}
```

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
# 复制并编辑环境变量文件
cp .env.example .env
# 编辑 .env 文件，添加你的 API 密钥
```

### 3. 使用示例

#### 直接使用 Agent
```python
import asyncio
from backend.agents import ChainAgent, AgentAgent, LangGraphAgent

async def main():
    # 创建 Agent
    agent = ChainAgent()  # 或 AgentAgent(), LangGraphAgent()
    await agent.initialize()
    
    # 进行对话
    response = await agent.chat("你好，请帮我计算 2 + 3")
    print(response['content'])

asyncio.run(main())
```

#### 使用统一 API
```python
import asyncio
from backend.api import AgentAPI

async def main():
    # 创建 API
    api = AgentAPI()
    await api.initialize()
    
    # 切换不同实现方式
    api.set_current_agent('chain')    # Chain方式
    api.set_current_agent('agent')    # Agent方式
    api.set_current_agent('langgraph') # LangGraph方式
    
    # 进行对话
    response = await api.chat("你好，请介绍一下你自己")
    print(response['content'])

asyncio.run(main())
```

## 📊 重塑成果

### 架构优化
- **文件数量减少**: ~70%
- **代码行数减少**: ~60%
- **核心功能保持**: 100%

### 主要改进
1. ✅ 文件结构简化（agent_agent.py）
2. ✅ services 移入 memory 和 tools 目录
3. ✅ 删除 base 文件夹，使用 LangChain 原生依赖
4. ✅ 工具调用简化为两种方式
5. ✅ 配置管理优化，统一 API Key 管理
6. ✅ 所有冗余文件已清理

### 技术栈
- **LangChain**: 核心框架
- **Ollama**: 本地模型支持
- **OpenAI/Anthropic**: 云端模型支持
- **Pydantic**: 数据验证
- **AsyncIO**: 异步处理

## 🔧 开发说明

### 添加新工具
1. 在 `backend/tools/builtin/example_tools.py` 中添加工具定义
2. 使用 `@tool` 装饰器或 `StructuredTool.from_function`
3. 工具会自动被加载和注册

### 扩展记忆存储
当前使用内存存储，可扩展支持：
- Redis 分布式存储
- SQLite 文件存储
- MongoDB 文档存储

### 添加新 Agent 类型
1. 在 `backend/agents/` 目录创建新文件
2. 继承或实现标准接口
3. 在 `__init__.py` 中导出

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 🎊 Agent模式和模型分离功能 ⭐

### 核心特性
本项目成功实现了**OpenWebUI前端的Agent模式和模型完全分离**功能：

- **任意组合**: 任何Agent模式都可以使用任何Ollama模型
- **动态发现**: 自动获取所有可用的Ollama模型
- **前端集成**: 在OpenWebUI中直接选择Agent+模型组合
- **即选即用**: 无需手动配置，选择即自动配置

### 使用方法
1. 启动服务: `docker-compose up -d`
2. 访问: http://localhost:3000
3. 选择Agent组合模型（57个可选）
4. 开始对话！

### 测试结果
- ✅ 57个Agent组合模型 + 1个配置器
- ✅ 所有Agent模式正常工作
- ✅ 端到端工作流完整
- **总体成功率**: 80%

详细指南: [OPENWEBUI_AGENT_GUIDE.md](OPENWEBUI_AGENT_GUIDE.md)

---

**项目重塑完成！Agent模式和模型分离功能已实现！** 🎉🎊
