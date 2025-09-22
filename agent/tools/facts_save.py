"""
Facts Save Tool - saving new facts.
Saves and retrieves facts from the knowledge base.
"""

import logging
from typing import Type, Dict, Any, Optional, List
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from ..memory.memory_manager import MemoryManager


class FactsSaveInput(BaseModel):
    """Input schema for facts save tool."""
    action: str = Field(
        description="Action to perform: 'save' (store new fact), 'get' (retrieve facts), or 'categories' (list categories)"
    )
    category: Optional[str] = Field(
        default=None,
        description="Fact category (required for 'save', optional filter for 'get')"
    )
    fact: Optional[str] = Field(
        default=None,
        description="Fact content to save (required for 'save' action)"
    )
    source: Optional[str] = Field(
        default=None,
        description="Source of the fact (optional for 'save' action)"
    )
    confidence: Optional[float] = Field(
        default=1.0,
        description="Confidence level 0.0-1.0 (optional for 'save' action)"
    )
    min_confidence: Optional[float] = Field(
        default=0.0,
        description="Minimum confidence level for filtering facts (optional for 'get' action)"
    )


class FactsSaveTool(BaseTool):
    """
    Tool for saving and retrieving facts from the knowledge base.
    Organizes information by categories with confidence levels.
    """

    name: str = "facts_save"
    description: str = (
        "Save important facts and information to the knowledge base, or retrieve previously saved facts. "
        "Facts are organized by categories and can have confidence levels. "
        "Useful for remembering key information, decisions, and learned facts."
    )
    args_schema: Type[BaseModel] = FactsSaveInput
    memory_manager: Optional[MemoryManager] = None

    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        """
        Initialize facts save tool.

        Args:
            memory_manager: Memory manager instance
        """
        super().__init__()
        if memory_manager is None:
            raise ValueError("memory_manager is required for FactsSaveTool")
        self.memory_manager = memory_manager

    def _run(self,
             action: str,
             category: Optional[str] = None,
             fact: Optional[str] = None,
             source: Optional[str] = None,
             confidence: Optional[float] = 1.0,
             min_confidence: Optional[float] = 0.0) -> str:
        """
        Execute facts operation.

        Args:
            action: Action to perform
            category: Fact category
            fact: Fact content
            source: Fact source
            confidence: Confidence level
            min_confidence: Minimum confidence for filtering

        Returns:
            Result of the operation
        """
        try:
            if self.memory_manager is None:
                return "Memory manager not available"

            if action == "save":
                return self._save_fact(category, fact, source, confidence)
            elif action == "get":
                return self._get_facts(category, min_confidence)
            elif action == "categories":
                return self._get_categories()
            else:
                return f"Invalid action '{action}'. Use 'save', 'get', or 'categories'."

        except Exception as e:
            logging.error(f"Facts tool failed: {e}")
            return f"Error with facts: {str(e)}"

    def _save_fact(self,
                   category: Optional[str],
                   fact: Optional[str],
                   source: Optional[str],
                   confidence: Optional[float]) -> str:
        """Save a fact to the knowledge base."""
        if not category:
            return "Category is required for saving a fact."

        if not fact:
            return "Fact content is required for saving."

        # Validate confidence
        if confidence is None:
            confidence = 1.0
        elif not (0.0 <= confidence <= 1.0):
            return "Confidence must be between 0.0 and 1.0."

        # Save fact
        success = self.memory_manager.save_fact(
            category=category,
            fact=fact,
            source=source,
            confidence=confidence
        )

        if success:
            confidence_percent = round(confidence * 100, 1)
            source_text = f" (source: {source})" if source else ""
            return f"✅ Fact saved in '{category}' category with {confidence_percent}% confidence{source_text}:\\n\\n{fact}"
        else:
            return "❌ Failed to save fact."

    def _get_facts(self, category: Optional[str], min_confidence: Optional[float]) -> str:
        """Get facts from the knowledge base."""
        if min_confidence is None:
            min_confidence = 0.0

        facts = self.memory_manager.get_facts(
            category=category,
            min_confidence=min_confidence
        )

        if not facts:
            filter_text = f" in category '{category}'" if category else ""
            confidence_text = f" with confidence >= {min_confidence}" if min_confidence > 0 else ""
            return f"📝 No facts found{filter_text}{confidence_text}."

        # Format facts
        formatted_facts = []
        if category:
            formatted_facts.append(f"📝 Facts in '{category}' category:")
        else:
            formatted_facts.append("📝 All facts:")

        formatted_facts.append("=" * 50)

        current_category = None
        for i, fact_data in enumerate(facts):
            fact_category = fact_data.get("category", "Unknown")
            fact_content = fact_data.get("fact", "No content")
            fact_confidence = fact_data.get("confidence", 0.0)
            fact_source = fact_data.get("source")
            fact_created = fact_data.get("created_at", "Unknown time")

            # Group by category if showing all categories
            if not category and fact_category != current_category:
                if current_category is not None:
                    formatted_facts.append("")
                formatted_facts.append(f"📂 {fact_category.title()}:")
                formatted_facts.append("-" * 30)
                current_category = fact_category

            # Format timestamp
            if "T" in fact_created:
                fact_created = fact_created.split("T")[0]

            confidence_percent = round(fact_confidence * 100, 1)
            confidence_emoji = "🟢" if fact_confidence >= 0.8 else "🟡" if fact_confidence >= 0.5 else "🔴"

            # Format fact entry
            fact_entry = f"{confidence_emoji} {fact_content}"
            if fact_source:
                fact_entry += f"\\n   📚 Source: {fact_source}"
            fact_entry += f"\\n   📅 Added: {fact_created} | 📊 Confidence: {confidence_percent}%"

            formatted_facts.append(fact_entry)
            formatted_facts.append("")

        formatted_facts.append("=" * 50)
        formatted_facts.append(f"Total: {len(facts)} fact(s)")

        return "\\n".join(formatted_facts)

    def _get_categories(self) -> str:
        """Get all fact categories."""
        facts = self.memory_manager.get_facts()

        if not facts:
            return "📂 No fact categories found. Save some facts first!"

        # Count facts by category
        category_counts = {}
        total_confidence_by_category = {}

        for fact_data in facts:
            category = fact_data.get("category", "Unknown")
            confidence = fact_data.get("confidence", 0.0)

            if category not in category_counts:
                category_counts[category] = 0
                total_confidence_by_category[category] = 0.0

            category_counts[category] += 1
            total_confidence_by_category[category] += confidence

        # Sort categories by fact count
        sorted_categories = sorted(
            category_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        formatted_categories = ["📂 Fact Categories:"]
        formatted_categories.append("=" * 40)

        for category, count in sorted_categories:
            avg_confidence = total_confidence_by_category[category] / count
            confidence_percent = round(avg_confidence * 100, 1)
            confidence_emoji = "🟢" if avg_confidence >= 0.8 else "🟡" if avg_confidence >= 0.5 else "🔴"

            formatted_categories.append(
                f"{confidence_emoji} {category.title()}: {count} fact(s) "
                f"(avg confidence: {confidence_percent}%)"
            )

        formatted_categories.append("=" * 40)
        formatted_categories.append(f"Total categories: {len(category_counts)}")
        formatted_categories.append(f"Total facts: {sum(category_counts.values())}")

        return "\\n".join(formatted_categories)

    async def _arun(self,
                    action: str,
                    category: Optional[str] = None,
                    fact: Optional[str] = None,
                    source: Optional[str] = None,
                    confidence: Optional[float] = 1.0,
                    min_confidence: Optional[float] = 0.0) -> str:
        """Async version of facts save tool."""
        return self._run(action, category, fact, source, confidence, min_confidence)