# 🐳 Docker 部署指南

本目录包含LangChain Agent项目的Docker部署文件。

## 📁 文件说明

- `docker-compose.yml` - Docker编排配置文件（标准模式）
- `docker-compose.dev.yml` - 开发模式配置文件
- `docker-compose.fast.yml` - 快速构建配置文件（国内镜像源）
- `Dockerfile.backend` - LangChain后端容器构建文件
- `Dockerfile.backend.fast` - 快速构建Dockerfile（国内镜像源）
- `Dockerfile.gradio` - Gradio界面容器构建文件
- `.dockerignore` - Docker构建忽略文件
- `start.sh` - Linux/Mac启动脚本
- `start.bat` - Windows启动脚本

## 🚀 快速启动

### 方式1: 使用启动脚本（推荐）

#### Linux/Mac
```bash
cd docker
chmod +x start.sh
./start.sh
```

#### Windows
```cmd
cd docker
start.bat
```

### 方式2: 直接使用docker-compose

#### 🚀 快速构建模式（国内用户推荐）
```bash
cd docker
docker-compose -f docker-compose.fast.yml up -d --build
```

#### 🔧 开发模式（代码热更新）
```bash
cd docker
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

#### 🏭 生产模式
```bash
cd docker
# 启动OpenWebUI + 后端
docker-compose up -d

# 启动Gradio + 后端
docker-compose --profile gradio up -d

# 仅启动后端
docker-compose up -d langchain-backend
```

## 🌐 访问地址

- **OpenWebUI前端**: http://localhost:3000
- **Gradio界面**: http://localhost:7860
- **LangChain API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## ⚙️ 环境配置

### 创建环境变量文件
在项目根目录创建 `.env` 文件：

```bash
# OpenAI配置（可选）
OPENAI_API_KEY=your_openai_key

# Anthropic配置（可选）
ANTHROPIC_API_KEY=your_anthropic_key

# OpenWebUI密钥
WEBUI_SECRET_KEY=your-secret-key-here

# Ollama配置（如果Ollama在其他地址）
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

### OpenWebUI配置

1. 访问 http://localhost:3000
2. 注册/登录账户
3. 进入 **设置** > **连接** > **OpenAI API**
4. 配置连接:
   - **API Base URL**: `http://langchain-backend:8000/v1`
   - **API Key**: `dummy-key`（任意值）
5. 选择模型:
   - `langchain-chain` - Chain Agent
   - `langchain-agent` - Agent Agent
   - `langchain-langgraph` - LangGraph Agent

## 🔧 常用命令

### 快速构建模式
```bash
# 启动快速构建
docker-compose -f docker-compose.fast.yml up -d --build

# 查看状态
docker-compose -f docker-compose.fast.yml ps

# 查看日志
docker-compose -f docker-compose.fast.yml logs -f

# 停止服务
docker-compose -f docker-compose.fast.yml down
```

### 标准模式
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up -d --build

# 清理所有数据
docker-compose down -v
```

### 开发模式
```bash
# 启动开发模式
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 查看开发日志
docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

# 停止开发模式
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
```

## 📊 服务监控

### 健康检查
后端服务包含健康检查端点：
```bash
curl http://localhost:8000/health
```

### 日志查看
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f langchain-backend
docker-compose logs -f openwebui
```

## 🛠️ 故障排除

### 常见问题

1. **构建速度慢**
   ```bash
   # 国内用户推荐使用快速构建模式
   docker-compose -f docker-compose.fast.yml up -d --build

   # 或使用启动脚本选择选项5
   start.bat  # Windows
   ./start.sh # Linux/Mac
   ```

2. **网络连接问题**
   ```bash
   # 方案1: 使用快速构建模式（已配置国内镜像源）
   docker-compose -f docker-compose.fast.yml up -d --build

   # 方案2: 配置Docker代理
   # Docker Desktop > Settings > Resources > Proxies
   # 启用Manual proxy configuration
   ```

3. **端口占用**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :3000
   netstat -tulpn | grep :8000

   # 停止所有相关容器
   docker-compose down
   docker-compose -f docker-compose.fast.yml down
   ```

4. **Docker权限问题**
   ```bash
   # Linux添加用户到docker组
   sudo usermod -aG docker $USER
   ```

5. **容器启动失败**
   ```bash
   # 查看详细错误信息
   docker-compose logs langchain-backend

   # 重新构建（无缓存）
   docker-compose build --no-cache
   ```

6. **数据持久化**
   ```bash
   # 数据存储在Docker卷中
   docker volume ls
   docker volume inspect docker_openwebui-data
   ```

### 重置环境
```bash
# 停止并删除所有容器和卷
docker-compose down -v

# 删除镜像（可选）
docker-compose down --rmi all

# 重新启动
docker-compose up -d --build
```

## 📊 构建模式对比

| 模式 | 构建时间 | 网络要求 | 适用场景 | 特点 |
|------|----------|----------|----------|------|
| 🚀 快速构建 | 2-5分钟 | 国内网络 | 首次部署 | 国内镜像源加速 |
| 🔧 开发模式 | 首次较慢 | 标准网络 | 日常开发 | 代码热更新 |
| 🏭 生产模式 | 10-20分钟 | 标准网络 | 生产部署 | 性能优化 |

### 🚀 快速构建模式（推荐国内用户）

**特点**：
- ⚡ **构建速度**: 2-5分钟完成
- 🇨🇳 **国内优化**: 阿里云Debian源 + 清华PyPI源
- 🔧 **网络友好**: 专为中国网络环境优化
- ✅ **功能完整**: 与标准模式功能完全相同

**使用方式**：
```bash
# 启动脚本方式
start.bat  # 选择选项5

# 直接命令方式
docker-compose -f docker-compose.fast.yml up -d --build
```

## 📝 开发模式

### 开发模式 vs 生产模式

#### 🔧 开发模式（推荐开发时使用）
```bash
# 启动开发模式 - 支持代码热更新
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 或使用启动脚本选择选项4
./start.sh  # Linux/Mac
start.bat   # Windows
```

**开发模式特点**：
- ✅ **代码热更新**: 修改源码立即生效，无需重新构建
- ✅ **实时调试**: 支持断点调试和日志输出
- ✅ **快速迭代**: 修改代码后立即看到效果
- ⚠️ **仅限开发**: 不适合生产环境

#### 🚀 生产模式
```bash
# 启动生产模式 - 代码打包到镜像中
docker-compose up -d

# 代码更改后需要重新构建
docker-compose up -d --build
```

**生产模式特点**：
- ✅ **性能优化**: 代码预编译，启动更快
- ✅ **安全隔离**: 代码完全封装在镜像中
- ✅ **部署稳定**: 不依赖外部文件系统
- ❌ **更新需重建**: 代码更改需要重新构建镜像

### 开发工作流程

1. **首次启动**:
   ```bash
   # 开发模式启动
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```

2. **修改代码**:
   - 直接编辑 `backend/` 或 `main/` 目录下的文件
   - 保存后自动生效，无需重启容器

3. **添加新依赖**:
   ```bash
   # 修改 requirements.txt 后需要重新构建
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
   ```

4. **查看日志**:
   ```bash
   docker-compose logs -f langchain-backend
   ```

## 🔒 安全注意事项

1. 修改默认的 `WEBUI_SECRET_KEY`
2. 在生产环境中使用HTTPS
3. 限制API访问权限
4. 定期更新容器镜像
