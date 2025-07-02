#!/usr/bin/env python3
"""
LangChain Agent 应用启动器
支持三种主要启动方式：Gradio、OpenWebUI、纯后端

使用方式：
python main/app.py gradio      # Gradio Web界面
python main/app.py openwebui   # OpenWebUI兼容服务器
python main/app.py backend     # 纯后端交互模式
"""

import sys
import argparse
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


def start_gradio():
    """启动Gradio Web界面"""
    print("🎨 启动Gradio Web界面...")
    print("📱 访问地址: http://localhost:7860")
    print("💡 功能: 完整的Web界面，支持Agent切换和工具调用")
    
    from frontend.gradio_app import main
    main()


def start_openwebui():
    """启动OpenWebUI兼容服务器"""
    print("🌐 启动OpenWebUI兼容服务器...")
    print("📱 API地址: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    print("💡 用途: 为OpenWebUI前端提供后端API")
    print("\n🔧 OpenWebUI前端配置:")
    print("   1. 下载OpenWebUI: docker run -d -p 3000:8080 ghcr.io/open-webui/open-webui:main")
    print("   2. 访问: http://localhost:3000")
    print("   3. 设置 > 连接 > OpenAI API")
    print("   4. API Base URL: http://localhost:8000/v1")
    print("   5. API Key: 任意值（不验证）")
    print("   6. 模型: langchain-chain, langchain-agent, langchain-langgraph")
    
    from backend.api.openwebui_server import main
    main()


async def start_backend():
    """启动纯后端交互模式"""
    print("💬 启动纯后端交互模式...")
    print("💡 功能: 命令行交互，支持Agent切换和多轮对话")
    print("📝 命令:")
    print("   - 'quit' 退出")
    print("   - 'clear' 清除历史")
    print("   - 'switch <agent>' 切换Agent (chain/agent/langgraph)")
    print("   - 'test' 运行测试")
    print("   - 'models' 测试模型切换")
    
    from backend.api.api import AgentAPI
    
    # 初始化
    api = AgentAPI()
    await api.initialize()
    session_id = "interactive_session"
    
    print(f"\n✅ 系统初始化完成，当前Agent: chain")
    print("=" * 50)
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n👤 你: ").strip()
            
            if user_input.lower() == 'quit':
                print("👋 再见！")
                break
            elif user_input.lower() == 'clear':
                await api.clear_memory(session_id)
                print("🗑️ 历史已清除")
                continue
            elif user_input.lower().startswith('switch '):
                agent_type = user_input[7:].strip()
                if agent_type in ["chain", "agent", "langgraph"]:
                    api.set_current_agent(agent_type)
                    print(f"🔄 已切换到 {agent_type} Agent")
                else:
                    print("❌ 无效的Agent类型，支持: chain, agent, langgraph")
                continue
            elif user_input.lower() == 'test':
                await run_agent_test()
                continue
            elif user_input.lower() == 'models':
                await run_model_test()
                continue
            elif not user_input:
                continue
            
            # 发送消息
            response = await api.chat(
                message=user_input,
                session_id=session_id
            )
            
            if response.get("success"):
                content = response.get("content", "")
                print(f"🤖 助手: {content}")
                
                tool_calls = response.get("tool_calls", [])
                if tool_calls:
                    print(f"🔧 使用了 {len(tool_calls)} 个工具")
            else:
                print(f"❌ 错误: {response.get('error', 'Unknown error')}")
                
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 异常: {e}")


async def run_agent_test():
    """运行Agent测试"""
    print("\n🔧 运行Agent测试...")
    
    try:
        from backend.agents.chain_agent import ChainAgent
        from backend.agents.agent_agent import AgentAgent
        
        # 测试ChainAgent
        print("1. 测试ChainAgent...")
        chain_agent = ChainAgent("ollama", "qwen2.5:7b")
        result = await chain_agent.initialize()
        print(f"   ChainAgent: {'✅ 成功' if result else '❌ 失败'}")
        
        # 测试AgentAgent
        print("2. 测试AgentAgent...")
        agent_agent = AgentAgent("ollama", "qwen2.5:7b")
        result = await agent_agent.initialize()
        print(f"   AgentAgent: {'✅ 成功' if result else '❌ 失败'}")
        
        print("✅ Agent测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")


async def run_model_test():
    """运行模型切换测试"""
    print("\n🔄 运行模型切换测试...")
    
    try:
        from backend.api.api import AgentAPI
        
        api = AgentAPI()
        await api.initialize()
        
        # 测试对话
        response = await api.chat(
            message="你好，请简单介绍一下你自己",
            session_id="test_session"
        )
        
        if response.get("success"):
            print(f"✅ 模型响应正常")
            print(f"   内容: {response.get('content', '')[:100]}...")
        else:
            print(f"❌ 模型响应失败: {response.get('error')}")
            
    except Exception as e:
        print(f"❌ 模型测试失败: {e}")


def show_help():
    """显示帮助信息"""
    print("""
🚀 LangChain Agent 应用启动器

支持的启动方式:
  1 | gradio      🎨 Gradio Web界面 (推荐新手)
  2 | openwebui   🌐 OpenWebUI兼容服务器 (专业用户)
  3 | backend     💬 纯后端交互模式 (开发者)

使用示例:
  python main/app.py 1           # 启动Gradio界面
  python main/app.py gradio      # 同上
  python main/app.py 2           # 启动OpenWebUI服务器
  python main/app.py openwebui   # 同上
  python main/app.py 3           # 启动命令行模式
  python main/app.py backend     # 同上

Docker部署:
  docker-compose up              # 启动OpenWebUI + 后端
  docker-compose --profile gradio up  # 启动Gradio + 后端

特性:
  ✅ 三种Agent实现 (Chain, Agent, LangGraph)
  ✅ 多种工具支持 (计算器, 搜索, 自定义等)
  ✅ 持久化记忆 (SQLite存储)
  ✅ 多轮对话支持
  ✅ 模型切换支持 (Ollama, OpenAI, Anthropic)

环境要求:
  🐍 Python 3.11+
  🔧 Conda环境: langchain_agent_env
""")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="LangChain Agent 应用启动器",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "mode",
        nargs="?",
        help="启动模式: 1/gradio, 2/openwebui, 3/backend"
    )
    
    args = parser.parse_args()
    
    if not args.mode:
        show_help()
        return
    
    print("🚀 LangChain Agent 应用启动器")
    print("=" * 60)
    
    try:
        # 数字映射
        mode_mapping = {
            "1": "gradio",
            "2": "openwebui",
            "3": "backend"
        }

        # 获取实际模式
        actual_mode = mode_mapping.get(args.mode, args.mode)

        if actual_mode == "gradio":
            start_gradio()
        elif actual_mode == "openwebui":
            start_openwebui()
        elif actual_mode == "backend":
            asyncio.run(start_backend())
        else:
            show_help()
            
    except KeyboardInterrupt:
        print("\n👋 用户中断，退出")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
