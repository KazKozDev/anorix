"""
LangChain Agent with Ollama Integration
A modular AI agent system with tool calling capabilities and Virtual Friend support.
"""

from .core import OllamaAgent
from .tool_manager import ToolManager
from .virtual_friend import VirtualFriend

__version__ = "2.0.0"
__all__ = ["OllamaAgent", "ToolManager", "VirtualFriend"]