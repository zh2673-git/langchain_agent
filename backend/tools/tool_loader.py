"""
工具自动加载器
自动发现和加载工具目录中的所有工具
"""
import os
import importlib
import inspect
from pathlib import Path
from typing import List, Dict, Any, Type

from ..base.tool_base import ToolBase, tool_registry
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ToolLoader:
    """工具自动加载器"""
    
    def __init__(self):
        self.loaded_tools = {}
        self.tool_directories = [
            "backend.tools.langchain_native"
        ]
    
    def discover_tools(self) -> List[Type[ToolBase]]:
        """自动发现所有工具类"""
        discovered_tools = []
        
        for tool_dir in self.tool_directories:
            try:
                discovered_tools.extend(self._discover_tools_in_directory(tool_dir))
            except Exception as e:
                logger.error(f"Failed to discover tools in {tool_dir}: {e}")
        
        return discovered_tools
    
    def _discover_tools_in_directory(self, module_path: str) -> List[Type[ToolBase]]:
        """在指定目录中发现工具"""
        tools = []
        
        try:
            # 将模块路径转换为文件系统路径
            path_parts = module_path.split('.')
            base_path = Path(__file__).parent.parent.parent
            
            for part in path_parts:
                base_path = base_path / part
            
            if not base_path.exists():
                logger.warning(f"Tool directory does not exist: {base_path}")
                return tools
            
            # 遍历目录中的所有Python文件
            for file_path in base_path.glob("*.py"):
                if file_path.name.startswith("__"):
                    continue
                
                try:
                    # 构建模块名
                    module_name = f"{module_path}.{file_path.stem}"
                    
                    # 动态导入模块
                    module = importlib.import_module(module_name)
                    
                    # 查找工具类
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if (obj != ToolBase and 
                            issubclass(obj, ToolBase) and 
                            obj.__module__ == module_name):
                            tools.append(obj)
                            logger.info(f"Discovered tool: {name} in {module_name}")
                
                except Exception as e:
                    logger.error(f"Failed to load module {module_name}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to discover tools in directory {module_path}: {e}")
        
        return tools
    
    async def load_all_tools(self) -> List[ToolBase]:
        """加载所有发现的工具"""
        tool_classes = self.discover_tools()
        loaded_tools = []
        
        for tool_class in tool_classes:
            try:
                # 创建工具实例
                tool_instance = tool_class()
                
                # 初始化工具
                if await tool_instance.initialize():
                    loaded_tools.append(tool_instance)
                    self.loaded_tools[tool_instance.name] = tool_instance
                    
                    # 注册到工具注册表
                    tool_registry.register(tool_instance)
                    
                    logger.info(f"Successfully loaded tool: {tool_instance.name}")
                else:
                    logger.error(f"Failed to initialize tool: {tool_class.__name__}")
            
            except Exception as e:
                logger.error(f"Failed to load tool {tool_class.__name__}: {e}")
        
        return loaded_tools
    
    def get_loaded_tools(self) -> Dict[str, ToolBase]:
        """获取已加载的工具"""
        return self.loaded_tools.copy()
    
    def get_tool_by_name(self, name: str) -> ToolBase:
        """根据名称获取工具"""
        return self.loaded_tools.get(name)
    
    def reload_tools(self) -> List[ToolBase]:
        """重新加载所有工具"""
        # 清空已加载的工具
        self.loaded_tools.clear()
        tool_registry.clear()
        
        # 重新加载
        import asyncio
        return asyncio.run(self.load_all_tools())
    
    def add_tool_directory(self, module_path: str):
        """添加工具目录"""
        if module_path not in self.tool_directories:
            self.tool_directories.append(module_path)
            logger.info(f"Added tool directory: {module_path}")
    
    def remove_tool_directory(self, module_path: str):
        """移除工具目录"""
        if module_path in self.tool_directories:
            self.tool_directories.remove(module_path)
            logger.info(f"Removed tool directory: {module_path}")


# 全局工具加载器实例
tool_loader = ToolLoader()


async def auto_load_tools() -> List[ToolBase]:
    """自动加载所有工具的便捷函数"""
    return await tool_loader.load_all_tools()


def get_all_loaded_tools() -> Dict[str, ToolBase]:
    """获取所有已加载工具的便捷函数"""
    return tool_loader.get_loaded_tools()


def get_tool(name: str) -> ToolBase:
    """根据名称获取工具的便捷函数"""
    return tool_loader.get_tool_by_name(name)


def add_custom_tool_directory(path: str):
    """添加自定义工具目录的便捷函数"""
    tool_loader.add_tool_directory(path)


# 工具配置文件支持
def load_tools_from_config(config_path: str = None) -> List[ToolBase]:
    """从配置文件加载工具"""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "tools_config.json")
    
    if not os.path.exists(config_path):
        logger.info(f"Tool config file not found: {config_path}, using auto-discovery")
        return tool_loader.reload_tools()
    
    try:
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 添加配置中的工具目录
        for directory in config.get("tool_directories", []):
            tool_loader.add_tool_directory(directory)
        
        # 重新加载工具
        return tool_loader.reload_tools()
    
    except Exception as e:
        logger.error(f"Failed to load tools from config: {e}")
        return tool_loader.reload_tools()


# 创建默认的工具配置文件
def create_default_config():
    """创建默认的工具配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "tools_config.json")
    
    if os.path.exists(config_path):
        return
    
    default_config = {
        "tool_directories": [
            "backend.tools.langchain_native"
        ],
        "disabled_tools": [],
        "tool_settings": {}
    }
    
    try:
        import json
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created default tool config: {config_path}")
    except Exception as e:
        logger.error(f"Failed to create default config: {e}")


# 初始化时创建默认配置
create_default_config()
