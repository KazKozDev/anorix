"""
Long-term memory (SQL) implementation.
Stores conversations, user profile, facts, and statistics in SQLite database.
"""

import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path


class LongTermMemory:
    """
    Long-term memory for persistent structured data storage.
    Uses SQLite database for reliable storage of conversations, profile, and facts.
    """

    def __init__(self, db_path: str = "data/conversations.db"):
        """
        Initialize long-term memory.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # User profile table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profile (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Facts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    fact TEXT NOT NULL,
                    source TEXT,
                    confidence REAL DEFAULT 1.0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    date TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_statistics_date ON statistics(date)")

            conn.commit()

    def save_conversation(self, session_id: str, role: str, content: str,
                         metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Save a conversation message.

        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Additional metadata

        Returns:
            Message ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations (session_id, role, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                role,
                content,
                datetime.now().isoformat(),
                json.dumps(metadata) if metadata else None
            ))
            conn.commit()
            return cursor.lastrowid

    def get_conversation_history(self, session_id: Optional[str] = None,
                                days: Optional[int] = None,
                                limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history.

        Args:
            session_id: Filter by session ID
            days: Get conversations from last N days
            limit: Limit number of results

        Returns:
            List of conversation messages
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM conversations WHERE 1=1"
            params = []

            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)

            if days:
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                query += " AND timestamp >= ?"
                params.append(cutoff_date)

            query += " ORDER BY timestamp DESC"

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            columns = [desc[0] for desc in cursor.description]
            conversations = []
            for row in rows:
                conv = dict(zip(columns, row))
                if conv['metadata']:
                    conv['metadata'] = json.loads(conv['metadata'])
                conversations.append(conv)

            return conversations

    def update_profile(self, key: str, value: Any) -> None:
        """
        Update user profile information.

        Args:
            key: Profile key
            value: Profile value
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_profile (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, json.dumps(value), datetime.now().isoformat()))
            conn.commit()

    def get_profile(self) -> Dict[str, Any]:
        """
        Get user profile.

        Returns:
            User profile dictionary
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM user_profile")
            rows = cursor.fetchall()

            profile = {}
            for key, value in rows:
                try:
                    profile[key] = json.loads(value)
                except json.JSONDecodeError:
                    profile[key] = value

            return profile

    def save_fact(self, category: str, fact: str, source: Optional[str] = None,
                  confidence: float = 1.0) -> int:
        """
        Save a fact to the knowledge base.

        Args:
            category: Fact category
            fact: Fact content
            source: Source of the fact
            confidence: Confidence level (0.0-1.0)

        Returns:
            Fact ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO facts (category, fact, source, confidence)
                VALUES (?, ?, ?, ?)
            """, (category, fact, source, confidence))
            conn.commit()
            return cursor.lastrowid

    def get_facts(self, category: Optional[str] = None,
                  min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """
        Get facts from the knowledge base.

        Args:
            category: Filter by category
            min_confidence: Minimum confidence level

        Returns:
            List of facts
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM facts WHERE confidence >= ?"
            params = [min_confidence]

            if category:
                query += " AND category = ?"
                params.append(category)

            query += " ORDER BY confidence DESC, created_at DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    def save_statistic(self, metric_name: str, metric_value: float,
                      metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Save a statistic.

        Args:
            metric_name: Name of the metric
            metric_value: Metric value
            metadata: Additional metadata

        Returns:
            Statistic ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO statistics (metric_name, metric_value, date, metadata)
                VALUES (?, ?, ?, ?)
            """, (
                metric_name,
                metric_value,
                datetime.now().date().isoformat(),
                json.dumps(metadata) if metadata else None
            ))
            conn.commit()
            return cursor.lastrowid

    def get_statistics(self, metric_name: Optional[str] = None,
                      days: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get statistics.

        Args:
            metric_name: Filter by metric name
            days: Get statistics from last N days

        Returns:
            List of statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM statistics WHERE 1=1"
            params = []

            if metric_name:
                query += " AND metric_name = ?"
                params.append(metric_name)

            if days:
                cutoff_date = (datetime.now() - timedelta(days=days)).date().isoformat()
                query += " AND date >= ?"
                params.append(cutoff_date)

            query += " ORDER BY date DESC, created_at DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            columns = [desc[0] for desc in cursor.description]
            statistics = []
            for row in rows:
                stat = dict(zip(columns, row))
                if stat['metadata']:
                    stat['metadata'] = json.loads(stat['metadata'])
                statistics.append(stat)

            return statistics

    def search_conversations(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search conversations by content.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching conversations
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM conversations
                WHERE content LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (f"%{query}%", limit))
            rows = cursor.fetchall()

            columns = [desc[0] for desc in cursor.description]
            conversations = []
            for row in rows:
                conv = dict(zip(columns, row))
                if conv['metadata']:
                    conv['metadata'] = json.loads(conv['metadata'])
                conversations.append(conv)

            return conversations

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Memory statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Count conversations
            cursor.execute("SELECT COUNT(*) FROM conversations")
            conv_count = cursor.fetchone()[0]

            # Count facts
            cursor.execute("SELECT COUNT(*) FROM facts")
            facts_count = cursor.fetchone()[0]

            # Count statistics
            cursor.execute("SELECT COUNT(*) FROM statistics")
            stats_count = cursor.fetchone()[0]

            # Database size
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

            return {
                "conversations_count": conv_count,
                "facts_count": facts_count,
                "statistics_count": stats_count,
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / (1024 * 1024), 2)
            }