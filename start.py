#!/usr/bin/env python3
"""
快速启动脚本 - 用于测试和开发
"""

import sys
import subprocess
from pathlib import Path

def main():
    """主函数"""
    print("🚀 LangChain Agent 快速启动")
    print("=" * 40)
    
    if len(sys.argv) < 2:
        print("使用方式:")
        print("  python start.py 1    # Gradio界面")
        print("  python start.py 2    # OpenWebUI服务器")
        print("  python start.py 3    # 后端交互")
        return
    
    mode = sys.argv[1]
    
    # 检查是否在正确的conda环境中
    try:
        result = subprocess.run(
            ["conda", "info", "--envs"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        if "langchain_agent_env" not in result.stdout:
            print("⚠️  建议创建专用conda环境:")
            print("   conda create -n langchain_agent_env python=3.11")
            print("   conda activate langchain_agent_env")
            print("   pip install -r requirements.txt")
            print()
    except:
        pass
    
    # 启动应用
    try:
        subprocess.run([sys.executable, "main/app.py", mode], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 启动失败: {e}")
        print("\n💡 可能的解决方案:")
        print("1. 确保已安装所有依赖: pip install -r requirements.txt")
        print("2. 确保Ollama正在运行: ollama serve")
        print("3. 检查Python环境是否正确")

if __name__ == "__main__":
    main()
