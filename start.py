#!/usr/bin/env python3
"""
LangChain Agent 项目启动脚本
"""

import sys
import os
import subprocess

def main():
    print("🤖 LangChain Agent 实践项目")
    print("=" * 50)
    print("完全基于 LangChain 官方源码实现的智能 Agent 系统")
    print()
    
    print("请选择启动方式:")
    print("1. 启动 Gradio Web 界面 (推荐)")
    print("2. 运行功能测试")
    print("3. 退出")
    print()
    
    while True:
        choice = input("请输入选择 (1-3): ").strip()
        
        if choice == "1":
            print("\n🚀 启动 Gradio Web 界面...")
            try:
                subprocess.run([sys.executable, "frontend/gradio_app.py"], check=True)
            except KeyboardInterrupt:
                print("\n👋 应用已停止")
            except Exception as e:
                print(f"\n❌ 启动失败: {e}")
            break
            
        elif choice == "2":
            print("\n🧪 运行功能测试...")
            try:
                subprocess.run([sys.executable, "test_langchain_implementation.py"], check=True)
            except Exception as e:
                print(f"\n❌ 测试失败: {e}")
            break
            
        elif choice == "3":
            print("\n👋 再见!")
            break
            
        else:
            print("❌ 无效选择，请输入 1-3")

if __name__ == "__main__":
    main()
