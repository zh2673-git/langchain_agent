#!/usr/bin/env python3
"""
刷新OpenWebUI模型缓存
强制OpenWebUI重新获取模型列表
"""

import requests
import json
import time


def clear_openwebui_cache():
    """清除OpenWebUI缓存"""
    print("🧹 清除OpenWebUI缓存...")
    
    try:
        # 尝试清除模型缓存
        response = requests.post(
            "http://localhost:3000/api/models/refresh",
            timeout=30
        )
        
        if response.status_code in [200, 404]:  # 404表示接口不存在，但不影响
            print("   ✅ 缓存清除请求已发送")
        else:
            print(f"   ⚠️  缓存清除响应: {response.status_code}")
            
    except Exception as e:
        print(f"   ⚠️  缓存清除异常: {e}")


def force_model_refresh():
    """强制刷新模型列表"""
    print("🔄 强制刷新模型列表...")
    
    try:
        # 直接调用后端API获取模型
        backend_response = requests.get("http://localhost:8000/api/models", timeout=10)
        
        if backend_response.status_code == 200:
            backend_data = backend_response.json()
            backend_models = backend_data.get("data", [])
            
            print(f"   ✅ 后端API返回 {len(backend_models)} 个模型")
            
            # 显示Agent组合模型
            agent_combos = [m for m in backend_models if m.get("metadata", {}).get("type") == "agent_combo"]
            configurators = [m for m in backend_models if m.get("metadata", {}).get("type") == "configurator"]
            
            print(f"   🤖 Agent组合模型: {len(agent_combos)}")
            print(f"   🔧 配置器模型: {len(configurators)}")
            
            # 显示前几个模型示例
            print(f"\n   模型示例:")
            for model in backend_models[:5]:
                name = model.get("name", "")
                model_id = model.get("id", "")
                print(f"     - {name} ({model_id})")
            
            return True
        else:
            print(f"   ❌ 后端API失败: {backend_response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 刷新异常: {e}")
        return False


def test_openwebui_connection():
    """测试OpenWebUI连接"""
    print("🌐 测试OpenWebUI连接...")
    
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        
        if response.status_code == 200:
            print("   ✅ OpenWebUI前端可访问")
            return True
        else:
            print(f"   ❌ OpenWebUI前端失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 连接异常: {e}")
        return False


def check_model_api_endpoint():
    """检查模型API端点"""
    print("🔍 检查模型API端点...")
    
    endpoints = [
        "http://localhost:8000/api/models",
        "http://localhost:8000/v1/models", 
        "http://localhost:3000/api/models"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=10)
            print(f"   {endpoint}: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    models = data.get("data", []) if isinstance(data, dict) else data
                    model_count = len(models) if isinstance(models, list) else 0
                    print(f"     模型数量: {model_count}")
                except:
                    print(f"     响应格式异常")
            
        except Exception as e:
            print(f"   {endpoint}: 连接失败 - {e}")


def restart_openwebui_if_needed():
    """如果需要，重启OpenWebUI"""
    print("🔄 检查是否需要重启OpenWebUI...")
    
    try:
        # 检查OpenWebUI状态
        response = requests.get("http://localhost:3000", timeout=5)
        
        if response.status_code == 200:
            print("   ✅ OpenWebUI运行正常，无需重启")
            return True
        else:
            print("   ⚠️  OpenWebUI状态异常，建议重启")
            return False
            
    except Exception as e:
        print(f"   ❌ 无法连接OpenWebUI，建议重启: {e}")
        return False


def provide_manual_instructions():
    """提供手动操作说明"""
    print("\n📋 手动操作说明:")
    print("=" * 50)
    
    print("\n1. 🌐 打开浏览器访问:")
    print("   http://localhost:3000")
    
    print("\n2. 🔄 强制刷新页面:")
    print("   - 按 Ctrl+F5 (Windows)")
    print("   - 按 Cmd+Shift+R (Mac)")
    print("   - 或者清除浏览器缓存")
    
    print("\n3. 🔍 检查模型列表:")
    print("   - 点击模型选择器")
    print("   - 查找以下模型:")
    print("     🔗 Chain Agent + 模型名")
    print("     🛠️ Tool Agent + 模型名")
    print("     🕸️ Graph Agent + 模型名")
    print("     🔧 Agent配置器")
    
    print("\n4. 🚫 如果仍显示旧模型:")
    print("   - 检查浏览器开发者工具 (F12)")
    print("   - 查看网络请求")
    print("   - 确认API调用地址")
    
    print("\n5. 🔧 故障排除:")
    print("   - 重启Docker容器:")
    print("     docker-compose restart openwebui")
    print("   - 清除浏览器所有数据")
    print("   - 使用无痕模式访问")


def main():
    """主函数"""
    print("🎯 OpenWebUI模型缓存刷新")
    print("=" * 50)
    
    # 等待服务稳定
    print("⏳ 等待服务稳定...")
    time.sleep(5)
    
    results = {}
    
    # 1. 测试连接
    results["connection"] = test_openwebui_connection()
    
    # 2. 检查API端点
    check_model_api_endpoint()
    
    # 3. 强制刷新模型
    results["refresh"] = force_model_refresh()
    
    # 4. 清除缓存
    clear_openwebui_cache()
    
    # 5. 检查是否需要重启
    results["restart_needed"] = not restart_openwebui_if_needed()
    
    # 总结
    print("\n📊 刷新结果:")
    print("-" * 30)
    
    for test_name, result in results.items():
        status = "✅ 正常" if result else "❌ 异常"
        test_display = {
            "connection": "OpenWebUI连接",
            "refresh": "模型刷新", 
            "restart_needed": "需要重启"
        }.get(test_name, test_name)
        
        print(f"   {test_display}: {status}")
    
    # 提供说明
    provide_manual_instructions()
    
    print("\n🎊 重要提示:")
    print("   如果前端仍显示旧模型，请:")
    print("   1. 强制刷新浏览器 (Ctrl+F5)")
    print("   2. 清除浏览器缓存")
    print("   3. 使用无痕模式访问")
    print("   4. 检查浏览器开发者工具的网络请求")


if __name__ == "__main__":
    main()
