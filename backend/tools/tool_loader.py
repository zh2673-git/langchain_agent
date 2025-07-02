"""
统一工具加载器 - 支持多种工具类型
基于LangChain 2025标准，支持：
1. 内置示例工具
2. LangChain社区工具
3. 自定义工具
4. MCP工具

使用方式：
1. 在config.py中配置要加载的工具
2. 工具加载器会自动发现和加载
3. 统一注册到工具服务中
"""

import importlib
import inspect
from typing import List, Dict, Optional
from pathlib import Path
from langchain_core.tools import BaseTool

from ..config import config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class UnifiedToolLoader:
    """统一工具加载器"""
    
    def __init__(self):
        self.loaded_tools: List[BaseTool] = []
        self.tool_sources: Dict[str, str] = {}  # tool_name -> source_type
    
    async def load_all_tools(self) -> List[BaseTool]:
        """加载所有配置的工具"""
        self.loaded_tools.clear()
        self.tool_sources.clear()
        
        loading_config = config.TOOL_LOADING_CONFIG
        
        # 1. 加载内置示例工具
        if loading_config.get("auto_load_builtin", True):
            await self._load_builtin_tools()
        
        # 2. 加载LangChain社区工具
        if loading_config.get("auto_load_community", True):
            await self._load_community_tools()
        
        # 3. 加载自定义工具
        if loading_config.get("auto_load_custom", True):
            await self._load_custom_tools()
        
        # 4. 加载MCP工具
        if loading_config.get("auto_load_mcp", False):
            await self._load_mcp_tools()
        
        logger.info(f"Loaded {len(self.loaded_tools)} tools from {len(set(self.tool_sources.values()))} sources")
        return self.loaded_tools

    async def _load_tools_from_directory(self, directory: Path, source_type: str) -> List[BaseTool]:
        """从目录加载工具"""
        tools = []

        if not directory.exists():
            logger.info(f"{source_type} tools directory not found: {directory}")
            return tools

        # 扫描目录中的所有.py文件
        for file_path in directory.rglob("*.py"):
            if file_path.name.startswith("__") or file_path.name.startswith("test_"):
                continue

            try:
                file_tools = await self._load_tools_from_file(file_path)
                for tool in file_tools:
                    if self._is_tool_enabled(tool.name):
                        self.loaded_tools.append(tool)
                        self.tool_sources[tool.name] = source_type
                        tools.append(tool)
                        logger.debug(f"Loaded {source_type} tool: {tool.name} from {file_path.name}")
            except Exception as e:
                logger.warning(f"Failed to load tools from {file_path}: {e}")

        return tools

    async def _load_builtin_tools(self):
        """加载内置工具（从独立的.py文件）"""
        try:
            builtin_dir = Path(__file__).parent / "builtin"
            tools = await self._load_tools_from_directory(builtin_dir, "builtin")

            logger.info(f"Loaded {len(tools)} builtin tools")
        except Exception as e:
            logger.error(f"Failed to load builtin tools: {e}")
    
    async def _load_community_tools(self):
        """加载社区工具（从独立的.py文件）"""
        try:
            community_dir = Path(__file__).parent / "community"
            tools = await self._load_tools_from_directory(community_dir, "community")

            logger.info(f"Loaded {len(tools)} community tools")
        except Exception as e:
            logger.error(f"Failed to load community tools: {e}")
    
    async def _load_custom_tools(self):
        """加载自定义工具"""
        try:
            # 从backend/tools/custom目录加载
            custom_tools_dir = Path(__file__).parent / "custom"

            if not custom_tools_dir.exists():
                logger.info("Custom tools directory not found")
                return

            # 扫描自定义工具目录
            for file_path in custom_tools_dir.rglob("*.py"):
                if file_path.name.startswith("__") or file_path.name.startswith("test_"):
                    continue

                try:
                    tools = await self._load_tools_from_file(file_path)
                    for tool in tools:
                        self.loaded_tools.append(tool)
                        self.tool_sources[tool.name] = "custom"

                    if tools:
                        logger.info(f"Loaded {len(tools)} custom tools from {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to load custom tools from {file_path}: {e}")

        except Exception as e:
            logger.error(f"Failed to load custom tools: {e}")
    
    async def _load_mcp_tools(self):
        """加载MCP工具"""
        try:
            mcp_config = config.MCP_TOOLS_CONFIG
            if not mcp_config.get("enabled", False):
                logger.info("MCP tools disabled in config")
                return

            # 导入MCP加载器
            from .mcp.mcp_loader import get_mcp_loader

            # 加载MCP工具
            mcp_loader = get_mcp_loader()
            mcp_tools = await mcp_loader.load_mcp_tools()

            for tool in mcp_tools:
                self.loaded_tools.append(tool)
                self.tool_sources[tool.name] = "mcp"

            if mcp_tools:
                server_info = mcp_loader.get_server_info()
                logger.info(f"Loaded {len(mcp_tools)} MCP tools from {server_info['total_servers']} servers")

        except Exception as e:
            logger.error(f"Failed to load MCP tools: {e}")
    
    def _is_tool_enabled(self, tool_name: str) -> bool:
        """检查工具是否启用"""
        builtin_config = config.BUILTIN_TOOLS_CONFIG
        return builtin_config.get(tool_name, {}).get("enabled", True)
    
    async def _load_tools_from_file(self, file_path: Path) -> List[BaseTool]:
        """从文件加载工具"""
        tools = []
        
        try:
            # 动态导入模块
            spec = importlib.util.spec_from_file_location("custom_tool", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找工具对象
            for name, obj in inspect.getmembers(module):
                # 跳过私有属性和导入的类
                if name.startswith('_') or name in ['BaseTool', 'StructuredTool', 'tool', 'BaseModel', 'Field']:
                    continue

                if isinstance(obj, BaseTool):
                    tools.append(obj)
                elif callable(obj) and hasattr(obj, '__annotations__') and not inspect.isclass(obj):
                    # 只转换函数，不转换类
                    try:
                        from langchain_core.tools import tool
                        if hasattr(obj, '_langchain_tool'):  # 已经是@tool装饰的函数
                            tools.append(obj)
                        else:
                            # 尝试转换为工具
                            tool_obj = tool(obj)
                            tools.append(tool_obj)
                    except Exception as e:
                        logger.debug(f"Failed to convert {name} to tool: {e}")
                        pass
        
        except Exception as e:
            logger.error(f"Error loading tools from {file_path}: {e}")
        
        return tools
    
    # LangChain社区工具加载方法
    async def _load_wikipedia_tool(self) -> Optional[BaseTool]:
        """加载Wikipedia工具"""
        try:
            from langchain_community.tools import WikipediaQueryRun
            from langchain_community.utilities import WikipediaAPIWrapper
            
            wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
            return wikipedia
        except ImportError:
            logger.warning("Wikipedia tool requires: pip install wikipedia")
            return None
    
    async def _load_duckduckgo_tool(self) -> Optional[BaseTool]:
        """加载DuckDuckGo搜索工具"""
        try:
            from langchain_community.tools import DuckDuckGoSearchRun
            
            search = DuckDuckGoSearchRun()
            return search
        except ImportError:
            logger.warning("DuckDuckGo tool requires: pip install duckduckgo-search")
            return None
    
    async def _load_python_repl_tool(self) -> Optional[BaseTool]:
        """加载Python REPL工具"""
        try:
            from langchain_experimental.tools import PythonREPLTool
            
            python_repl = PythonREPLTool()
            return python_repl
        except ImportError:
            logger.warning("Python REPL tool requires: pip install langchain-experimental")
            return None
    
    async def _load_shell_tool(self) -> Optional[BaseTool]:
        """加载Shell工具"""
        try:
            from langchain_community.tools import ShellTool
            
            shell = ShellTool()
            return shell
        except ImportError:
            logger.warning("Shell tool not available")
            return None
    
    async def _load_requests_tool(self) -> Optional[BaseTool]:
        """加载Requests工具"""
        try:
            from langchain_community.tools import RequestsGetTool
            
            requests_tool = RequestsGetTool()
            return requests_tool
        except ImportError:
            logger.warning("Requests tool not available")
            return None
    
    async def _load_arxiv_tool(self) -> Optional[BaseTool]:
        """加载ArXiv工具"""
        try:
            from langchain_community.tools import ArxivQueryRun
            from langchain_community.utilities import ArxivAPIWrapper
            
            arxiv = ArxivQueryRun(api_wrapper=ArxivAPIWrapper())
            return arxiv
        except ImportError:
            logger.warning("ArXiv tool requires: pip install arxiv")
            return None
    
    async def _load_wolfram_tool(self) -> Optional[BaseTool]:
        """加载Wolfram Alpha工具"""
        try:
            api_key = config.get_api_key("wolfram")
            if not api_key:
                logger.warning("Wolfram Alpha tool requires API key")
                return None
            
            from langchain_community.tools import WolframAlphaQueryRun
            from langchain_community.utilities import WolframAlphaAPIWrapper
            
            wolfram = WolframAlphaQueryRun(
                api_wrapper=WolframAlphaAPIWrapper(wolfram_alpha_appid=api_key)
            )
            return wolfram
        except ImportError:
            logger.warning("Wolfram Alpha tool requires: pip install wolframalpha")
            return None
    
    async def _load_google_search_tool(self) -> Optional[BaseTool]:
        """加载Google搜索工具"""
        try:
            api_key = config.get_api_key("google")
            cse_id = config.GOOGLE_CSE_ID
            
            if not api_key or not cse_id:
                logger.warning("Google Search tool requires API key and CSE ID")
                return None
            
            from langchain_community.tools import GoogleSearchRun
            from langchain_community.utilities import GoogleSearchAPIWrapper
            
            search = GoogleSearchRun(
                api_wrapper=GoogleSearchAPIWrapper(
                    google_api_key=api_key,
                    google_cse_id=cse_id
                )
            )
            return search
        except ImportError:
            logger.warning("Google Search tool requires: pip install google-api-python-client")
            return None
    
    async def _load_bing_search_tool(self) -> Optional[BaseTool]:
        """加载Bing搜索工具"""
        try:
            api_key = config.get_api_key("bing")
            if not api_key:
                logger.warning("Bing Search tool requires API key")
                return None
            
            from langchain_community.tools import BingSearchRun
            from langchain_community.utilities import BingSearchAPIWrapper
            
            search = BingSearchRun(
                api_wrapper=BingSearchAPIWrapper(bing_subscription_key=api_key)
            )
            return search
        except ImportError:
            logger.warning("Bing Search tool not available")
            return None


# 全局工具加载器实例
_tool_loader_instance: Optional[UnifiedToolLoader] = None


def get_tool_loader() -> UnifiedToolLoader:
    """获取全局工具加载器实例"""
    global _tool_loader_instance
    if _tool_loader_instance is None:
        _tool_loader_instance = UnifiedToolLoader()
    return _tool_loader_instance
