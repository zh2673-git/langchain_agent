"""
Gradio前端界面
基于Gradio实现的Web界面，不修改后端代码

特点：
1. 简单易用的Web界面
2. 支持三种Agent切换
3. 实时聊天功能
4. 会话管理
5. 工具调用展示
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import gradio as gr
from typing import List, Tuple, Dict, Any
import json

# 导入后端API
from backend.api.api import AgentAPI


class GradioInterface:
    """Gradio界面管理器"""
    
    def __init__(self):
        self.api = AgentAPI()
        self.current_session_id = None
        self.initialized = False
    
    async def initialize(self):
        """初始化API"""
        if not self.initialized:
            success = await self.api.initialize()
            if success:
                self.initialized = True
                return "✅ 系统初始化成功"
            else:
                return "❌ 系统初始化失败"
        return "✅ 系统已初始化"
    
    def switch_agent(self, agent_type: str) -> str:
        """切换Agent类型"""
        try:
            success = self.api.set_current_agent(agent_type)
            if success:
                return f"✅ 已切换到 {agent_type} Agent"
            else:
                return f"❌ 切换到 {agent_type} Agent 失败"
        except Exception as e:
            return f"❌ 切换Agent失败: {str(e)}"
    
    async def chat(self, message: str, history: List[Tuple[str, str]]) -> Tuple[List[Tuple[str, str]], str]:
        """聊天功能"""
        if not self.initialized:
            await self.initialize()
        
        if not message.strip():
            return history, ""
        
        try:
            # 创建会话ID（如果没有）
            if not self.current_session_id:
                self.current_session_id = "gradio_session"
            
            # 调用后端API
            response = await self.api.chat(
                message=message,
                session_id=self.current_session_id
            )
            
            if response.get("success"):
                # 添加到历史记录
                history.append((message, response.get("content", "无响应")))
                
                # 如果有工具调用，显示工具信息
                tool_calls = response.get("tool_calls", [])
                if tool_calls:
                    tool_info = "\n\n🔧 工具调用:\n"
                    for call in tool_calls:
                        tool_info += f"- {call.get('tool', 'Unknown')}: {call.get('result', 'No result')}\n"
                    history[-1] = (message, response.get("content", "") + tool_info)
            else:
                error_msg = response.get("error", "未知错误")
                history.append((message, f"❌ 错误: {error_msg}"))
            
            return history, ""
            
        except Exception as e:
            history.append((message, f"❌ 系统错误: {str(e)}"))
            return history, ""
    
    def clear_chat(self) -> Tuple[List, str]:
        """清除聊天记录"""
        if self.current_session_id and self.initialized:
            try:
                # 异步清除会话（在同步函数中）
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.api.clear_memory(self.current_session_id))
                loop.close()
            except:
                pass
        
        self.current_session_id = None
        return [], "🗑️ 聊天记录已清除"
    
    def get_system_info(self) -> str:
        """获取系统信息"""
        if not self.initialized:
            return "系统未初始化"
        
        try:
            # 获取当前Agent信息
            current_agent = self.api.get_current_agent_info()
            
            info = f"""
## 🤖 当前Agent信息
- **类型**: {current_agent.get('type', 'Unknown')}
- **提供商**: {current_agent.get('provider', 'Unknown')}
- **模型**: {current_agent.get('model', 'Unknown')}
- **初始化状态**: {'✅' if current_agent.get('initialized') else '❌'}

## 🛠️ 工具信息
- **工具数量**: {current_agent.get('tools_count', 0)}
- **支持工具调用**: {'✅' if current_agent.get('supports_tools') else '❌'}

## 💾 记忆信息
- **记忆启用**: {'✅' if current_agent.get('memory_enabled') else '❌'}
- **当前会话**: {self.current_session_id or '无'}
"""
            return info
        except Exception as e:
            return f"获取系统信息失败: {str(e)}"


# 创建全局接口实例
interface = GradioInterface()


def create_gradio_app():
    """创建Gradio应用"""
    
    # 初始化函数
    async def init_system():
        return await interface.initialize()
    
    # 聊天函数（同步包装）
    def chat_wrapper(message, history):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(interface.chat(message, history))
            return result
        finally:
            loop.close()
    
    # 初始化函数（同步包装）
    def init_wrapper():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(init_system())
            return result
        finally:
            loop.close()
    
    # 创建Gradio界面
    with gr.Blocks(
        title="LangChain Agent 聊天界面",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1200px !important;
        }
        """
    ) as app:
        
        gr.Markdown("""
        # 🤖 LangChain Agent 聊天界面
        
        基于LangChain的智能Agent系统，支持三种实现方式和多种工具调用。
        """)
        
        with gr.Row():
            with gr.Column(scale=3):
                # 聊天界面
                chatbot = gr.Chatbot(
                    label="聊天记录",
                    height=500,
                    show_copy_button=True
                )
                
                with gr.Row():
                    msg_input = gr.Textbox(
                        label="输入消息",
                        placeholder="请输入您的消息...",
                        scale=4
                    )
                    send_btn = gr.Button("发送", variant="primary", scale=1)
                
                with gr.Row():
                    clear_btn = gr.Button("清除记录", variant="secondary")
                    init_btn = gr.Button("初始化系统", variant="primary")
            
            with gr.Column(scale=1):
                # 控制面板
                gr.Markdown("## ⚙️ 控制面板")
                
                agent_selector = gr.Radio(
                    choices=["chain", "agent", "langgraph"],
                    value="chain",
                    label="Agent类型",
                    info="选择不同的Agent实现方式"
                )
                
                switch_btn = gr.Button("切换Agent", variant="secondary")
                
                status_display = gr.Textbox(
                    label="状态信息",
                    value="请先初始化系统",
                    interactive=False,
                    lines=3
                )
                
                gr.Markdown("## 📊 系统信息")
                
                info_btn = gr.Button("刷新信息", variant="secondary")
                
                system_info = gr.Markdown(
                    value="点击'刷新信息'获取系统状态",
                    label="系统状态"
                )
        
        # 事件绑定
        
        # 发送消息
        def submit_message(message, history):
            return chat_wrapper(message, history)
        
        send_btn.click(
            submit_message,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, msg_input]
        )
        
        msg_input.submit(
            submit_message,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, msg_input]
        )
        
        # 清除记录
        clear_btn.click(
            interface.clear_chat,
            outputs=[chatbot, status_display]
        )
        
        # 初始化系统
        init_btn.click(
            init_wrapper,
            outputs=[status_display]
        )
        
        # 切换Agent
        switch_btn.click(
            interface.switch_agent,
            inputs=[agent_selector],
            outputs=[status_display]
        )
        
        # 刷新系统信息
        info_btn.click(
            interface.get_system_info,
            outputs=[system_info]
        )
    
    return app


def main():
    """主函数"""
    print("🚀 启动Gradio界面...")
    print("📱 访问地址: http://localhost:7860")
    print("🔧 支持的Agent类型: chain, agent, langgraph")
    print("💡 使用说明:")
    print("   1. 点击'初始化系统'按钮")
    print("   2. 选择Agent类型并点击'切换Agent'")
    print("   3. 开始聊天")

    app = create_gradio_app()

    # 启动应用
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        quiet=False
    )


if __name__ == "__main__":
    main()
