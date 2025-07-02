#!/bin/bash
# Docker启动脚本

set -e

echo "🐳 LangChain Agent Docker 启动器"
echo "=================================="

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 显示选项
echo "选择启动方式:"
echo "1. OpenWebUI + LangChain后端 (推荐)"
echo "2. Gradio + LangChain后端"
echo "3. 仅LangChain后端"
echo "4. 停止所有服务"
echo "5. 查看服务状态"
echo "6. 查看日志"

read -p "请选择 (1-6): " choice

case $choice in
    1)
        echo "🚀 启动OpenWebUI + LangChain后端..."
        docker-compose up -d
        echo "✅ 服务已启动"
        echo "📱 OpenWebUI: http://localhost:3000"
        echo "🔗 API文档: http://localhost:8000/docs"
        ;;
    2)
        echo "🚀 启动Gradio + LangChain后端..."
        docker-compose --profile gradio up -d
        echo "✅ 服务已启动"
        echo "📱 Gradio: http://localhost:7860"
        echo "🔗 API文档: http://localhost:8000/docs"
        ;;
    3)
        echo "🚀 启动仅LangChain后端..."
        docker-compose up -d langchain-backend
        echo "✅ 后端服务已启动"
        echo "🔗 API文档: http://localhost:8000/docs"
        ;;
    4)
        echo "🛑 停止所有服务..."
        docker-compose down
        echo "✅ 所有服务已停止"
        ;;
    5)
        echo "📊 服务状态:"
        docker-compose ps
        ;;
    6)
        echo "📋 服务日志:"
        docker-compose logs -f
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac
