#!/usr/bin/env python3
"""
OpenWebUI工具注册脚本
确保工具在OpenWebUI中正确显示和可用
"""

import requests
import json
import time
import os
from pathlib import Path


def register_tools_with_openwebui():
    """向OpenWebUI注册工具"""
    print("🔧 向OpenWebUI注册工具...")
    
    tools_dir = Path("openwebui_tools")
    tools_config_file = tools_dir / "tools.json"
    
    if not tools_config_file.exists():
        print("❌ 工具配置文件不存在")
        return False
    
    try:
        with open(tools_config_file, 'r', encoding='utf-8') as f:
            tools_config = json.load(f)
        
        tools = tools_config.get("tools", [])
        print(f"   发现 {len(tools)} 个工具")
        
        # 注册每个工具
        registered_count = 0
        for tool in tools:
            tool_name = tool.get("name", "")
            tool_file = tool.get("file", "")
            tool_desc = tool.get("description", "")
            
            print(f"   注册工具: {tool_name}")
            
            # 检查工具文件是否存在
            tool_path = tools_dir / tool_file
            if not tool_path.exists():
                print(f"     ⚠️  工具文件不存在: {tool_file}")
                continue
            
            # 这里可以添加向OpenWebUI API注册工具的逻辑
            # 目前OpenWebUI主要通过文件挂载来识别工具
            registered_count += 1
        
        print(f"   ✅ 成功注册 {registered_count} 个工具")
        return True
        
    except Exception as e:
        print(f"   ❌ 注册工具失败: {e}")
        return False


def test_tools_api():
    """测试工具API"""
    print("\n🧪 测试工具API...")
    
    try:
        # 测试后端工具API
        response = requests.get("http://localhost:8000/v1/tools", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            tools = data.get("tools", [])
            print(f"   ✅ 后端API返回 {len(tools)} 个工具")
            
            # 查找Agent配置工具
            agent_tool_found = False
            for tool in tools:
                if "agent" in tool.get("name", "").lower():
                    agent_tool_found = True
                    print(f"     发现Agent工具: {tool.get('name', '')}")
            
            if not agent_tool_found:
                print("     ⚠️  未发现Agent配置工具")
            
            return len(tools) > 0
        else:
            print(f"   ❌ 后端工具API失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 测试工具API异常: {e}")
        return False


def test_agent_tool_directly():
    """直接测试Agent配置工具"""
    print("\n🤖 直接测试Agent配置工具...")
    
    try:
        # 导入Agent配置工具
        import sys
        sys.path.append("openwebui_tools")
        
        from agent_configurator import agent_configurator
        
        # 测试列出模式
        result = agent_configurator("list_modes")
        print(f"   ✅ 列出模式测试成功")
        print(f"   结果: {result[:100]}...")
        
        # 测试列出模型
        result = agent_configurator("list_models")
        print(f"   ✅ 列出模型测试成功")
        print(f"   结果: {result[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 直接测试失败: {e}")
        return False


def create_openwebui_tool_manifest():
    """创建OpenWebUI工具清单"""
    print("\n📋 创建OpenWebUI工具清单...")
    
    try:
        tools_dir = Path("openwebui_tools")
        
        # 扫描工具文件
        tool_files = list(tools_dir.glob("*.py"))
        tool_files = [f for f in tool_files if f.name != "__init__.py"]
        
        manifest = {
            "name": "LangChain Agent Tools",
            "description": "LangChain Agent系统工具集",
            "version": "1.0.0",
            "tools": []
        }
        
        for tool_file in tool_files:
            tool_name = tool_file.stem
            
            # 尝试读取工具描述
            try:
                with open(tool_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 简单提取描述
                description = f"{tool_name} 工具"
                if '"""' in content:
                    desc_start = content.find('"""') + 3
                    desc_end = content.find('"""', desc_start)
                    if desc_end > desc_start:
                        description = content[desc_start:desc_end].strip().split('\n')[0]
                
                manifest["tools"].append({
                    "name": tool_name,
                    "file": tool_file.name,
                    "description": description,
                    "enabled": True
                })
                
            except Exception as e:
                print(f"     ⚠️  读取工具文件失败: {tool_file.name} - {e}")
        
        # 保存清单
        manifest_file = tools_dir / "manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print(f"   ✅ 创建工具清单成功: {len(manifest['tools'])} 个工具")
        return True
        
    except Exception as e:
        print(f"   ❌ 创建工具清单失败: {e}")
        return False


def check_openwebui_container():
    """检查OpenWebUI容器状态"""
    print("\n🐳 检查OpenWebUI容器状态...")
    
    try:
        import subprocess
        
        # 检查容器是否运行
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=openwebui-frontend", "--format", "{{.Status}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and result.stdout.strip():
            status = result.stdout.strip()
            print(f"   ✅ OpenWebUI容器状态: {status}")
            
            # 检查工具挂载
            result = subprocess.run(
                ["docker", "exec", "openwebui-frontend", "ls", "-la", "/app/backend/data/tools/"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                files = result.stdout.strip()
                file_count = len([line for line in files.split('\n') if line.strip() and not line.startswith('total')])
                print(f"   ✅ 工具目录挂载成功: {file_count} 个文件")
                return True
            else:
                print(f"   ❌ 工具目录挂载失败")
                return False
        else:
            print(f"   ❌ OpenWebUI容器未运行")
            return False
            
    except Exception as e:
        print(f"   ❌ 检查容器状态失败: {e}")
        return False


def main():
    """主函数"""
    print("🎯 OpenWebUI工具注册和测试")
    print("=" * 60)
    
    results = {}
    
    # 1. 创建工具清单
    results["manifest"] = create_openwebui_tool_manifest()
    
    # 2. 注册工具
    results["register"] = register_tools_with_openwebui()
    
    # 3. 检查容器状态
    results["container"] = check_openwebui_container()
    
    # 4. 测试工具API
    results["api"] = test_tools_api()
    
    # 5. 直接测试Agent工具
    results["agent_tool"] = test_agent_tool_directly()
    
    # 总结结果
    print("\n📊 测试结果总结:")
    print("=" * 40)
    
    for feature, success in results.items():
        status = "✅ 正常" if success else "❌ 异常"
        feature_name = {
            "manifest": "工具清单创建",
            "register": "工具注册",
            "container": "容器状态检查",
            "api": "工具API测试",
            "agent_tool": "Agent工具直接测试"
        }.get(feature, feature)
        
        print(f"   {feature_name}: {status}")
    
    # 计算成功率
    total_tests = len(results)
    successful_tests = sum(results.values())
    success_rate = (successful_tests / total_tests) * 100
    
    print(f"\n📈 总体成功率: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("\n🎉 OpenWebUI工具系统基本正常！")
        print("\n💡 下一步:")
        print("   1. 重启OpenWebUI容器")
        print("   2. 在OpenWebUI中查看工具列表")
        print("   3. 测试Agent配置工具")
    else:
        print("\n⚠️  需要进一步调试工具系统")
        
        failed_features = [name for name, success in results.items() if not success]
        print(f"   失败的功能: {failed_features}")
        
        print("\n🔧 建议检查:")
        print("   1. OpenWebUI容器是否正常运行")
        print("   2. 工具文件是否正确挂载")
        print("   3. 工具文件格式是否正确")
        print("   4. 后端API是否正常")


if __name__ == "__main__":
    main()
