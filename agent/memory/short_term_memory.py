"""
Short-term memory (RAM) implementation.
Stores current conversation context in memory for immediate access.
"""

from typing import List, Dict, Any, Optional
from collections import deque
from datetime import datetime
import logging


class ShortTermMemory:
    """
    Short-term memory for current conversation context.
    Keeps the last N messages in RAM for quick access.
    """

    def __init__(self, max_messages: int = 10):
        """
        Initialize short-term memory.

        Args:
            max_messages: Maximum number of messages to keep in memory
        """
        self.max_messages = max_messages
        self.messages = deque(maxlen=max_messages)
        self.logger = logging.getLogger(__name__)

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a message to short-term memory.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Additional metadata
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        self.messages.append(message)
        self.logger.debug(f"Added message to short-term memory: {role}")

    def get_recent_messages(self, count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get recent messages from short-term memory.

        Args:
            count: Number of messages to return (default: all)

        Returns:
            List of recent messages
        """
        if count is None:
            return list(self.messages)

        return list(self.messages)[-count:] if count > 0 else []

    def get_conversation_context(self) -> str:
        """
        Get conversation context as formatted string.

        Returns:
            Formatted conversation context
        """
        if not self.messages:
            return "No recent conversation history."

        context_lines = []
        for msg in self.messages:
            timestamp = msg["timestamp"][:19]  # Remove microseconds
            role = msg["role"].capitalize()
            content = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
            context_lines.append(f"[{timestamp}] {role}: {content}")

        return "\n".join(context_lines)

    def clear(self) -> None:
        """Clear all messages from short-term memory."""
        self.messages.clear()
        self.logger.debug("Cleared short-term memory")

    def get_last_user_message(self) -> Optional[Dict[str, Any]]:
        """
        Get the last user message.

        Returns:
            Last user message or None if not found
        """
        for msg in reversed(self.messages):
            if msg["role"] == "user":
                return msg
        return None

    def get_last_assistant_message(self) -> Optional[Dict[str, Any]]:
        """
        Get the last assistant message.

        Returns:
            Last assistant message or None if not found
        """
        for msg in reversed(self.messages):
            if msg["role"] == "assistant":
                return msg
        return None

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Memory statistics
        """
        return {
            "current_messages": len(self.messages),
            "max_messages": self.max_messages,
            "memory_usage_percent": (len(self.messages) / self.max_messages) * 100,
            "oldest_message_time": self.messages[0]["timestamp"] if self.messages else None,
            "newest_message_time": self.messages[-1]["timestamp"] if self.messages else None
        }