"""
Agent 实现模块
基于 LangChain 原生实现的 Agent 系统

三种LangChain实现方式：
- ChainAgent: 使用LangChain的Chain组合方式实现多轮对话、工具调用、记忆管理
- AgentAgent: 使用create_tool_calling_agent和AgentExecutor实现标准的LangChain Agent
- LangGraphAgent: 使用LangGraph实现更复杂的工作流和状态管理
"""
from .chain_agent import ChainAgent
from .agent_agent import AgentAgent
from .langgraph_agent import LangGraphAgent

__all__ = [
    "ChainAgent",
    "AgentAgent",
    "LangGraphAgent"
]
