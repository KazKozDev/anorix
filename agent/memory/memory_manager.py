"""
Memory Manager - coordinates all three memory layers.
Provides unified interface for the three-layer memory system.
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from .short_term_memory import ShortTermMemory
from .long_term_memory import LongTermMemory
from .smart_memory import SmartMemory


class MemoryManager:
    """
    Unified memory manager that coordinates all three memory layers:
    1. Short-term memory (RAM) - current conversation context
    2. Long-term memory (SQL) - persistent structured data
    3. Smart memory (Vector DB) - semantic search capabilities
    """

    def __init__(self,
                 short_term_max_messages: int = 10,
                 long_term_db_path: str = "data/conversations.db",
                 smart_memory_db_path: str = "data/vector_db",
                 smart_memory_collection: str = "conversations",
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize memory manager.

        Args:
            short_term_max_messages: Max messages in short-term memory
            long_term_db_path: Path to SQL database
            smart_memory_db_path: Path to vector database
            smart_memory_collection: Vector database collection name
            embedding_model: Embedding model for semantic search
        """
        self.logger = logging.getLogger(__name__)
        self.session_id = str(uuid.uuid4())

        # Initialize memory layers
        self.short_term = ShortTermMemory(max_messages=short_term_max_messages)
        self.long_term = LongTermMemory(db_path=long_term_db_path)

        # Initialize smart memory (optional, may fail if dependencies missing)
        self.smart_memory = None
        try:
            self.smart_memory = SmartMemory(
                db_path=smart_memory_db_path,
                collection_name=smart_memory_collection,
                embedding_model=embedding_model
            )
            self.logger.info("Smart memory initialized successfully")
        except ImportError as e:
            self.logger.warning(f"Smart memory not available: {e}")
        except Exception as e:
            self.logger.error(f"Failed to initialize smart memory: {e}")

    def add_message(self,
                   role: str,
                   content: str,
                   metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add message to all memory layers.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Additional metadata
        """
        # Add to short-term memory (RAM)
        self.short_term.add_message(role, content, metadata)

        # Add to long-term memory (SQL)
        try:
            self.long_term.save_conversation(
                session_id=self.session_id,
                role=role,
                content=content,
                metadata=metadata
            )
        except Exception as e:
            self.logger.error(f"Failed to save to long-term memory: {e}")

        # Add to smart memory (Vector DB)
        if self.smart_memory:
            try:
                self.smart_memory.add_conversation(
                    role=role,
                    content=content,
                    session_id=self.session_id,
                    metadata=metadata
                )
            except Exception as e:
                self.logger.error(f"Failed to save to smart memory: {e}")

    def get_conversation_context(self, include_timestamps: bool = True) -> str:
        """
        Get current conversation context from short-term memory.

        Args:
            include_timestamps: Whether to include timestamps

        Returns:
            Formatted conversation context
        """
        return self.short_term.get_conversation_context()

    def search_memories(self,
                       query: str,
                       method: str = "semantic",
                       limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search memories across different layers.

        Args:
            query: Search query
            method: Search method ("semantic", "text", "both")
            limit: Maximum number of results

        Returns:
            List of search results
        """
        results = []

        if method in ["semantic", "both"] and self.smart_memory:
            # Semantic search using vector similarity
            try:
                semantic_results = self.smart_memory.search_similar(
                    query=query,
                    n_results=limit
                )
                for result in semantic_results:
                    result["search_method"] = "semantic"
                    results.append(result)
            except Exception as e:
                self.logger.error(f"Semantic search failed: {e}")

        if method in ["text", "both"]:
            # Text search using SQL LIKE
            try:
                text_results = self.long_term.search_conversations(
                    query=query,
                    limit=limit
                )
                for result in text_results:
                    results.append({
                        "content": result["content"],
                        "metadata": {
                            "role": result["role"],
                            "session_id": result["session_id"],
                            "timestamp": result["timestamp"],
                            "id": result["id"]
                        },
                        "search_method": "text",
                        "similarity": 0.5  # Default similarity for text search
                    })
            except Exception as e:
                self.logger.error(f"Text search failed: {e}")

        # Remove duplicates and sort by similarity
        unique_results = {}
        for result in results:
            content = result["content"]
            if content not in unique_results or result.get("similarity", 0) > unique_results[content].get("similarity", 0):
                unique_results[content] = result

        final_results = list(unique_results.values())
        final_results.sort(key=lambda x: x.get("similarity", 0), reverse=True)

        return final_results[:limit]

    def get_conversation_history(self,
                               days: Optional[int] = None,
                               session_id: Optional[str] = None,
                               limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history from long-term memory.

        Args:
            days: Get conversations from last N days
            session_id: Filter by session ID (default: current session)
            limit: Limit number of results

        Returns:
            List of conversation messages
        """
        if session_id is None:
            session_id = self.session_id

        try:
            return self.long_term.get_conversation_history(
                session_id=session_id,
                days=days,
                limit=limit
            )
        except Exception as e:
            self.logger.error(f"Failed to get conversation history: {e}")
            return []

    def get_user_profile(self) -> Dict[str, Any]:
        """
        Get user profile from long-term memory.

        Returns:
            User profile dictionary
        """
        try:
            return self.long_term.get_profile()
        except Exception as e:
            self.logger.error(f"Failed to get user profile: {e}")
            return {}

    def update_user_profile(self, key: str, value: Any) -> bool:
        """
        Update user profile in long-term memory.

        Args:
            key: Profile key
            value: Profile value

        Returns:
            Success status
        """
        try:
            self.long_term.update_profile(key, value)
            return True
        except Exception as e:
            self.logger.error(f"Failed to update user profile: {e}")
            return False

    def save_fact(self,
                  category: str,
                  fact: str,
                  source: Optional[str] = None,
                  confidence: float = 1.0) -> bool:
        """
        Save a fact to long-term memory.

        Args:
            category: Fact category
            fact: Fact content
            source: Source of the fact
            confidence: Confidence level (0.0-1.0)

        Returns:
            Success status
        """
        try:
            self.long_term.save_fact(category, fact, source, confidence)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save fact: {e}")
            return False

    def get_facts(self,
                  category: Optional[str] = None,
                  min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """
        Get facts from long-term memory.

        Args:
            category: Filter by category
            min_confidence: Minimum confidence level

        Returns:
            List of facts
        """
        try:
            return self.long_term.get_facts(category, min_confidence)
        except Exception as e:
            self.logger.error(f"Failed to get facts: {e}")
            return []

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive memory statistics.

        Returns:
            Memory statistics from all layers
        """
        stats = {
            "session_id": self.session_id,
            "short_term": self.short_term.get_memory_stats(),
            "long_term": self.long_term.get_memory_stats()
        }

        if self.smart_memory:
            try:
                stats["smart_memory"] = self.smart_memory.get_memory_stats()
            except Exception as e:
                self.logger.error(f"Failed to get smart memory stats: {e}")
                stats["smart_memory"] = {"error": str(e)}
        else:
            stats["smart_memory"] = {"status": "not_available"}

        return stats

    def start_new_session(self) -> str:
        """
        Start a new conversation session.

        Returns:
            New session ID
        """
        self.session_id = str(uuid.uuid4())
        self.short_term.clear()
        self.logger.info(f"Started new session: {self.session_id}")
        return self.session_id

    def get_current_session_id(self) -> str:
        """
        Get current session ID.

        Returns:
            Current session ID
        """
        return self.session_id