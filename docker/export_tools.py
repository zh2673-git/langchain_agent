#!/usr/bin/env python3
"""
工具导出脚本
将LangChain工具导出为OpenWebUI可用的格式
"""

import sys
import os
import asyncio

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.tools.adapters.openwebui_exporter import export_tools_to_openwebui
from backend.tools.tool_service import get_tool_service
from backend.utils.logger import get_logger

logger = get_logger(__name__)


async def main():
    """主函数"""
    print("LangChain工具导出器")
    print("=" * 50)
    
    try:
        # 初始化工具服务
        print("初始化工具服务...")
        tool_service = get_tool_service()
        success = await tool_service.initialize()

        if not success:
            print("工具服务初始化失败")
            return False

        print(f"工具服务初始化成功，加载了 {len(tool_service.list_tool_names())} 个工具")
        
        # 列出所有工具
        tool_names = tool_service.list_tool_names()
        print(f"\n可用工具列表:")
        for i, tool_name in enumerate(tool_names, 1):
            print(f"   {i}. {tool_name}")

        # 导出工具
        print(f"\n导出工具到OpenWebUI格式...")
        success = export_tools_to_openwebui()

        if success:
            print("工具导出成功！")
            print(f"\n导出位置: docker/openwebui_tools/")
            print(f"导出数量: {len(tool_names)} 个工具")
            
            # 显示导出的文件
            export_dir = "openwebui_tools"
            if os.path.exists(export_dir):
                files = [f for f in os.listdir(export_dir) if f.endswith('.py')]
                print(f"\n导出的文件:")
                for file in files:
                    print(f"   - {file}")

            print(f"\n使用说明:")
            print(f"   1. 重启OpenWebUI服务")
            print(f"   2. 在OpenWebUI中查看工具列表")
            print(f"   3. 启用需要的工具")
            print(f"   4. 在对话中使用工具")

            return True
        else:
            print("工具导出失败")
            return False

    except Exception as e:
        print(f"导出过程出错: {e}")
        logger.error(f"Export failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
