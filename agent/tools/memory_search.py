"""
Memory Search Tool - search in past conversations.
Semantic and text search across conversation history.
"""

import logging
from typing import Type, Dict, Any, List, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from ..memory.memory_manager import MemoryManager


class MemorySearchInput(BaseModel):
    """Input schema for memory search tool."""
    query: str = Field(
        description="Search query to find relevant conversations"
    )
    method: str = Field(
        default="semantic",
        description="Search method: 'semantic' (meaning-based), 'text' (keyword-based), or 'both'"
    )
    limit: int = Field(
        default=5,
        description="Maximum number of search results to return"
    )


class MemorySearchTool(BaseTool):
    """
    Tool for searching through conversation history using semantic and text search.
    Finds relevant past conversations based on meaning or keywords.
    """

    name: str = "memory_search"
    description: str = (
        "Search through conversation history to find relevant past discussions. "
        "Use semantic search to find conversations with similar meaning, "
        "or text search to find specific keywords. "
        "Useful for recalling previous topics, decisions, or information."
    )
    args_schema: Type[BaseModel] = MemorySearchInput
    memory_manager: Optional[MemoryManager] = None

    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        """
        Initialize memory search tool.

        Args:
            memory_manager: Memory manager instance
        """
        super().__init__()
        if memory_manager is None:
            raise ValueError("memory_manager is required for MemorySearchTool")
        self.memory_manager = memory_manager

    def _run(self, query: str, method: str = "semantic", limit: int = 5) -> str:
        """
        Execute memory search.

        Args:
            query: Search query
            method: Search method
            limit: Maximum results

        Returns:
            Formatted search results
        """
        try:
            if self.memory_manager is None:
                return "Memory manager not available"

            # Validate method
            if method not in ["semantic", "text", "both"]:
                return f"Invalid search method '{method}'. Use 'semantic', 'text', or 'both'."

            # Perform search
            results = self.memory_manager.search_memories(
                query=query,
                method=method,
                limit=limit
            )

            if not results:
                return f"No relevant conversations found for query: '{query}'"

            # Format results
            formatted_results = []
            formatted_results.append(f"🔍 Found {len(results)} relevant conversation(s) for: '{query}'\\n")

            for i, result in enumerate(results, 1):
                content = result.get("content", "")
                metadata = result.get("metadata", {})
                similarity = result.get("similarity", 0)
                search_method = result.get("search_method", "unknown")

                # Truncate long content
                if len(content) > 200:
                    content = content[:200] + "..."

                # Format timestamp
                timestamp = metadata.get("timestamp", "Unknown time")
                if "T" in timestamp:
                    timestamp = timestamp.split("T")[0] + " " + timestamp.split("T")[1][:8]

                role = metadata.get("role", "unknown")
                similarity_percent = round(similarity * 100, 1)

                formatted_results.append(
                    f"{i}. [{timestamp}] {role.title()}: {content}\\n"
                    f"   📊 Relevance: {similarity_percent}% ({search_method} search)\\n"
                )

            return "\\n".join(formatted_results)

        except Exception as e:
            logging.error(f"Memory search failed: {e}")
            return f"Error searching memory: {str(e)}"

    async def _arun(self, query: str, method: str = "semantic", limit: int = 5) -> str:
        """Async version of memory search."""
        return self._run(query, method, limit)