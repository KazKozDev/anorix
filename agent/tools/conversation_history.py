"""
Conversation History Tool - history for period.
Retrieves conversation history for specific time periods.
"""

import logging
from typing import Type, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from ..memory.memory_manager import MemoryManager


class ConversationHistoryInput(BaseModel):
    """Input schema for conversation history tool."""
    days: Optional[int] = Field(
        default=None,
        description="Number of days to look back (default: all history)"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Specific session ID to filter (default: current session)"
    )
    limit: Optional[int] = Field(
        default=20,
        description="Maximum number of messages to return"
    )
    role_filter: Optional[str] = Field(
        default=None,
        description="Filter by role: 'user', 'assistant', or 'system'"
    )


class ConversationHistoryTool(BaseTool):
    """
    Tool for retrieving conversation history from different time periods.
    Can filter by session, time range, role, and limit results.
    """

    name: str = "conversation_history"
    description: str = (
        "Retrieve conversation history from specific time periods. "
        "Can filter by number of days, session ID, message role, or limit results. "
        "Useful for reviewing past conversations and understanding context."
    )
    args_schema: Type[BaseModel] = ConversationHistoryInput
    memory_manager: Optional[MemoryManager] = None

    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        """
        Initialize conversation history tool.

        Args:
            memory_manager: Memory manager instance
        """
        super().__init__()
        if memory_manager is None:
            raise ValueError("memory_manager is required for ConversationHistoryTool")
        self.memory_manager = memory_manager

    def _run(self,
             days: Optional[int] = None,
             session_id: Optional[str] = None,
             limit: Optional[int] = 20,
             role_filter: Optional[str] = None) -> str:
        """
        Execute conversation history retrieval.

        Args:
            days: Number of days to look back
            session_id: Session ID filter
            limit: Maximum number of messages
            role_filter: Role filter

        Returns:
            Formatted conversation history
        """
        try:
            if self.memory_manager is None:
                return "Memory manager not available"

            # Get conversation history
            conversations = self.memory_manager.get_conversation_history(
                days=days,
                session_id=session_id,
                limit=limit
            )

            if not conversations:
                filter_text = self._build_filter_description(days, session_id, role_filter)
                return f"📜 No conversation history found{filter_text}."

            # Apply role filter if specified
            if role_filter:
                conversations = [
                    conv for conv in conversations
                    if conv.get("role", "").lower() == role_filter.lower()
                ]

                if not conversations:
                    return f"📜 No messages found from role '{role_filter}'."

            # Format conversations
            return self._format_conversations(conversations, days, session_id, role_filter)

        except Exception as e:
            logging.error(f"Conversation history retrieval failed: {e}")
            return f"Error retrieving conversation history: {str(e)}"

    def _build_filter_description(self,
                                 days: Optional[int],
                                 session_id: Optional[str],
                                 role_filter: Optional[str]) -> str:
        """Build description of applied filters."""
        filters = []

        if days is not None:
            filters.append(f"last {days} day(s)")

        if session_id:
            session_short = session_id[:8] + "..." if len(session_id) > 8 else session_id
            filters.append(f"session {session_short}")

        if role_filter:
            filters.append(f"role '{role_filter}'")

        if filters:
            return f" with filters: {', '.join(filters)}"
        return ""

    def _format_conversations(self,
                            conversations: list,
                            days: Optional[int],
                            session_id: Optional[str],
                            role_filter: Optional[str]) -> str:
        """Format conversations for display."""
        formatted_lines = []

        # Header
        header = "📜 Conversation History"
        filter_desc = self._build_filter_description(days, session_id, role_filter)
        if filter_desc:
            header += filter_desc

        formatted_lines.append(header)
        formatted_lines.append("=" * 60)

        # Group conversations by session
        sessions = {}
        for conv in conversations:
            conv_session_id = conv.get("session_id", "unknown")
            if conv_session_id not in sessions:
                sessions[conv_session_id] = []
            sessions[conv_session_id].append(conv)

        # Sort sessions by most recent activity
        sorted_sessions = sorted(
            sessions.items(),
            key=lambda x: max(conv.get("timestamp", "") for conv in x[1]),
            reverse=True
        )

        for session_key, session_conversations in sorted_sessions:
            # Session header (only if multiple sessions)
            if len(sessions) > 1:
                session_short = session_key[:8] + "..." if len(session_key) > 8 else session_key
                formatted_lines.append(f"\\n🔗 Session: {session_short}")
                formatted_lines.append("-" * 30)

            # Sort conversations in session by timestamp
            session_conversations.sort(
                key=lambda x: x.get("timestamp", ""),
                reverse=False  # Oldest first within session
            )

            for conv in session_conversations:
                role = conv.get("role", "unknown")
                content = conv.get("content", "")
                timestamp = conv.get("timestamp", "Unknown time")

                # Format timestamp
                if "T" in timestamp:
                    date_part = timestamp.split("T")[0]
                    time_part = timestamp.split("T")[1][:8]
                    timestamp = f"{date_part} {time_part}"

                # Role emoji
                role_emoji = self._get_role_emoji(role)

                # Truncate long content
                if len(content) > 300:
                    content = content[:300] + "..."

                # Format message
                formatted_lines.append(
                    f"[{timestamp}] {role_emoji} {role.title()}: {content}"
                )
                formatted_lines.append("")

        # Footer
        formatted_lines.append("=" * 60)
        formatted_lines.append(f"Total messages: {len(conversations)}")

        if len(sessions) > 1:
            formatted_lines.append(f"Sessions: {len(sessions)}")

        # Memory stats
        memory_stats = self.memory_manager.get_memory_stats()
        short_term_count = memory_stats.get("short_term", {}).get("current_messages", 0)
        long_term_count = memory_stats.get("long_term", {}).get("conversations_count", 0)

        formatted_lines.append(f"Memory: {short_term_count} recent, {long_term_count} total")

        return "\\n".join(formatted_lines)

    def _get_role_emoji(self, role: str) -> str:
        """Get emoji for message role."""
        role_emojis = {
            "user": "👤",
            "assistant": "🤖",
            "system": "⚙️"
        }
        return role_emojis.get(role.lower(), "💬")

    async def _arun(self,
                    days: Optional[int] = None,
                    session_id: Optional[str] = None,
                    limit: Optional[int] = 20,
                    role_filter: Optional[str] = None) -> str:
        """Async version of conversation history tool."""
        return self._run(days, session_id, limit, role_filter)