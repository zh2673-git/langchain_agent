# 🌐 OpenWebUI前端使用指南

## 📋 功能概览

OpenWebUI前端现在已经集成了LangChain Agent系统，提供以下功能：

### 🤖 Agent模型选择
- **langchain-chain**: Chain Agent (基于Runnable接口)
- **langchain-agent**: Tool Agent (支持工具调用)
- **langchain-langgraph**: Graph Agent (基于状态图)

### 🔄 模型切换功能
每个Agent都支持切换底层Ollama模型：
- **qwen2.5:7b** - 通义千问2.5 7B模型
- **qwen2.5:14b** - 通义千问2.5 14B模型  
- **llama3.1:8b** - Meta Llama 3.1 8B模型
- **mistral:7b** - Mistral 7B模型

### 🔧 工具系统
- **48个可用工具** - 包括计算、文本处理、数据分析等
- **自动转换** - LangChain工具自动转换为OpenWebUI格式
- **模块化管理** - 每个工具独立的.py文件

## 🚀 使用方法

### 1. 访问前端界面
```
http://localhost:3000
```

### 2. 选择Agent模型
在模型选择器中选择：
- `langchain-chain` - 适合简单的对话和任务
- `langchain-agent` - 适合需要工具调用的复杂任务
- `langchain-langgraph` - 适合多步骤的复杂工作流

### 3. 切换底层模型
有两种方式切换模型：

#### 方式1: 通过对话
```
请帮我切换chain Agent到llama3.1:8b模型
```

#### 方式2: 通过API
```bash
curl -X POST "http://localhost:8000/v1/models/langchain-chain/switch-backend" \
  -H "Content-Type: application/json" \
  -d '{"backend_model": "llama3.1:8b"}'
```

### 4. 使用工具功能
在对话中直接请求工具功能：

#### 计算工具
```
请帮我计算 123 * 456 + 789
```

#### 时间工具
```
现在几点了？
```

#### 文本处理
```
请帮我分析这段文本的统计信息：[你的文本]
```

#### 数据分析
```
请分析这些数字：1,2,3,4,5,6,7,8,9,10
```

#### 实用工具
```
请生成一个12位的强密码
```

#### 文件操作
```
请在workspace目录创建一个test.txt文件，内容是"Hello World"
```

## 🔧 高级功能

### 模型信息查询
```
请显示所有Agent的模型信息
```

### 工具列表查询
```
请列出所有可用的工具
```

### 批量操作
```
请帮我：
1. 计算 100 * 200
2. 获取当前时间
3. 生成一个UUID
4. 创建一个包含计算结果的文件
```

## 📊 功能验证

### 测试脚本
运行以下脚本验证功能：
```bash
cd docker
python test_openwebui_features.py
```

### 预期结果
- ✅ 配置API正常
- ✅ 模型切换API正常  
- ✅ OpenWebUI工具正常
- ✅ 前端访问正常
- ✅ 工具执行正常

## 🛠️ 故障排除

### 看不到Agent模型
1. 确认服务正常启动：`docker-compose ps`
2. 检查后端日志：`docker logs langchain-agent-backend`
3. 重启服务：`docker-compose restart`

### 工具不可用
1. 检查工具挂载：`ls docker/openwebui_tools/`
2. 重新导出工具：`python export_tools.py`
3. 重启OpenWebUI：`docker-compose restart openwebui-frontend`

### 模型切换失败
1. 确认Ollama服务运行：检查Ollama是否可访问
2. 检查模型是否已下载：`ollama list`
3. 查看切换日志：`docker logs langchain-agent-backend`

### 前端无响应
1. 检查端口占用：确认3000端口可用
2. 清除浏览器缓存
3. 检查网络连接

## 📈 性能优化

### 模型选择建议
- **轻量任务**: 使用 qwen2.5:7b
- **复杂任务**: 使用 qwen2.5:14b 或 llama3.1:8b
- **特殊需求**: 使用 mistral:7b

### Agent选择建议
- **简单对话**: langchain-chain
- **工具调用**: langchain-agent
- **复杂工作流**: langchain-langgraph

## 🔮 扩展功能

### 添加新工具
1. 在 `backend/tools/custom/` 创建新的.py文件
2. 运行 `python export_tools.py` 导出
3. 重启服务使工具生效

### 添加新模型
1. 在Ollama中下载新模型
2. 更新配置文件中的可用模型列表
3. 重启服务

### 自定义Agent
1. 在 `backend/agents/` 创建新的Agent类
2. 在API中注册新的Agent
3. 更新前端模型列表

## 💡 最佳实践

1. **选择合适的Agent**: 根据任务复杂度选择Agent类型
2. **合理使用工具**: 充分利用工具功能提高效率
3. **模型切换**: 根据性能需求动态切换模型
4. **错误处理**: 遇到问题时查看日志和错误信息
5. **定期更新**: 保持工具和模型的最新状态

现在你可以在OpenWebUI中享受完整的LangChain Agent体验！🎉
