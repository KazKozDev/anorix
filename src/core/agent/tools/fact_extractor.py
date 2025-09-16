"""
LLM-based Fact Extractor tool.
Extracts structured personal/user-related facts from free-form messages using the local LLM (Ollama).
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from src.core.config.settings import load_llm_settings


class LLMFactExtractor:
    """
    Uses an LLM to extract normalized facts from a single message.
    Returns a JSON string, which is a list of objects with fields:
      - type: user_fact | preference | relationship | location | occupation | event | other
      - field: optional short field label (e.g., name, age, hobby)
      - value: canonical text value of the fact
      - relation: optional relation type (e.g., boyfriend, girlfriend, spouse)
      - confidence: float 0..1
      - language: detected language code
      - source: "chat"
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,
        verbose: bool = False,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        # Load centralized defaults if args are not provided
        _settings = load_llm_settings()
        self.model_name = model_name or _settings.get("model_name")
        self.base_url = base_url or _settings.get("base_url")
        self.temperature = temperature if temperature is not None else _settings.get("temperature", 0.0)
        self.verbose = verbose
        try:
            self.llm = ChatOllama(
                model=self.model_name,
                base_url=self.base_url,
                temperature=self.temperature,
                verbose=self.verbose,
            )
        except Exception as e:
            self.logger.error(f"Failed to init ChatOllama for fact extractor: {e}")
            raise

        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                (
                    "You are a precise information extraction assistant. "
                    "Given a single user message, extract any concrete, persistable facts about the user. "
                    "Return STRICTLY a JSON array (no prose), where each element is an object with keys: "
                    "type, field, value, confidence, language, source, and optionally relation. "
                    "Use type='user_fact' for personal facts; 'preference' for likes/hobbies/interests; "
                    "'relationship' for partners/family (set relation like 'boyfriend','girlfriend','spouse'); "
                    "'occupation' for jobs; 'location' for city/country; use 'other' if unsure. "
                    "Set source='chat'. confidence in 0..1. language as ISO code ('ru'/'en'). "
                    "If no facts can be safely extracted, return []. "
                ),
            ),
            (
                "human",
                (
                    "Message:\n{message}\n\n"
                    "Return JSON array only. Do not include any prose. If nothing is extractable, return []."
                ),
            ),
        ])

    class ExtractInput(BaseModel):
        message: str = Field(description="A single user message to analyze for facts")
        context: Optional[str] = Field(default=None, description="Optional context window (recent chat history and relevant RAG snippets)")

    def get_tool(self) -> StructuredTool:
        return StructuredTool(
            name="fact_extractor",
            description=(
                "Analyze a user message with an LLM and extract structured, persistable facts "
                "(user facts, preferences, relationships, occupation, location). Accepts optional context. "
                "Returns a JSON string array."
            ),
            args_schema=self.ExtractInput,
            func=self._extract_structured,
        )

    def _extract_structured(self, message: str, context: Optional[str] = None) -> str:
        try:
            chain = self.prompt | self.llm
            # Prepend context to the message if provided
            composite = (
                f"[CONTEXT]\n{context}\n\n[MESSAGE]\n{message}" if context else message
            )
            out = chain.invoke({"message": composite})
            text = getattr(out, "content", str(out)) if out is not None else "[]"
            # Validate JSON format; if invalid, attempt to fix simple wrapping issues
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return json.dumps(parsed, ensure_ascii=False)
            except Exception:
                # Try to find JSON array substring
                import re
                m = re.search(r"\[[\s\S]*\]", text)
                if m:
                    try:
                        parsed = json.loads(m.group(0))
                        if isinstance(parsed, list):
                            return json.dumps(parsed, ensure_ascii=False)
                    except Exception:
                        pass
            # Fallback empty
            return "[]"
        except Exception as e:
            self.logger.error(f"Fact extraction failed: {e}")
            return "[]"
