"""
Core agent implementation with Ollama LLM integration.
"""

import logging
import json
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from langchain_ollama.chat_models import ChatOllama as Ollama
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
import re

from .tool_manager import ToolManager
from .callbacks import DetailedAgentCallbackHandler, SimpleObservationHandler
from src.core.config.settings import load_llm_settings


class OllamaAgent:
    """
    Main agent class with Ollama LLM integration and tool calling capabilities.
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,
        config_path: Optional[str] = None,
        verbose: bool = False
    ):
        """
        Initialize the Ollama agent.
        
        Args:
            model_name: Name of the Ollama model to use
            base_url: Ollama server URL
            temperature: LLM temperature setting
            config_path: Path to configuration file
            verbose: Enable verbose logging
        """
        self.logger = self._setup_logging()
        self.verbose = verbose
        
        # Load configuration if provided
        self.config = self._load_config(config_path) if config_path else {}
        
        # Centralized LLM settings with override order: env/settings -> YAML -> passed args
        settings = load_llm_settings()
        # If args provided explicitly, they take precedence; else fall back to YAML/env settings
        self.model_name = model_name or self.config.get('model_name', settings.get('model_name'))
        self.base_url = base_url or self.config.get('base_url', settings.get('base_url'))
        self.temperature = temperature if temperature is not None else self.config.get('temperature', settings.get('temperature', 0.1))
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Initialize tool manager with RAG support
        self.tool_manager = ToolManager(enable_rag=True)
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output",
        )
        
        # System message
        self.system_message = self._get_system_message()
        
        # Initialize callbacks for detailed observation
        self.callback_handler = DetailedAgentCallbackHandler(self.logger, self.verbose)
        
        # Initialize agent
        self.agent = None
        self._initialize_agent()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # Remove existing handlers to prevent duplicate logs
        for h in list(logger.handlers):
            logger.removeHandler(h)

        # IMPORTANT: prevent propagation to root to avoid duplicate lines,
        # since web_ui/app.py also configures the root logger
        logger.propagate = False

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                self.logger.info(f"Configuration loaded from {config_path}")
                return config
            else:
                self.logger.warning(f"Configuration file not found: {config_path}")
                return {}
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return {}
    
    def _initialize_llm(self) -> Ollama:
        """Initialize Ollama LLM."""
        try:
            llm = Ollama(
                model=self.model_name,
                temperature=self.temperature,
                base_url=self.base_url,
                verbose=self.verbose
            )
            self.logger.info(f"Ollama LLM initialized with model: {self.model_name}")
            self.logger.debug(f"LLM object type: {type(llm)}")
            self.logger.debug(f"LLM object dir: {dir(llm)}")
            return llm
        except Exception as e:
            self.logger.error(f"Failed to initialize Ollama LLM: {e}")
            raise
    
    def _get_system_message(self) -> str:
        """Get system message for the agent."""
        default_message = """
You are a helpful AI assistant with access to various tools.
Use the available tools to accomplish the user's tasks.
Always explain which tool you are using and why.
If the required information is not available, say so honestly.
Respond in the user's language; if the user writes in Russian, respond in Russian.

 TOOLING RULES:
 - For downloading binary files (e.g., PDFs), use the `http_download` tool. Do NOT use the web scraper or web_search for direct PDF URLs.
 - For saving local files, prefer the structured `file_write` tool (args: path, content). Do NOT embed large JSON inside string commands.
 - For RAG ingestion, use `rag_management` (actions: add_text, add_file, add_directory). Avoid inventing abstracts; fetch abstracts from authoritative sources (e.g., arXiv abs pages) or cite the source.
 - Avoid running `web_search` on a direct URL. If a direct URL is given, act directly (download or open) instead of searching it.

 PERSONAL FACTS VIA RAG (CRITICAL):
 - Store and retrieve user-related facts using RAG tools, not a separate personal memory.
 - When the user shares new personal info, call `rag_management` with action='add_text' and metadata tags like type=user_fact, source=chat (avoid braces in examples).
 - Before answering questions about the user, call `rag_retrieval` with the query and optionally filter by metadata (e.g., type=user_fact). Use retrieved snippets to personalize the answer.
 - NEVER answer "I don't know" about the user without first attempting retrieval via `rag_retrieval`.

 RAG CHECK BEFORE EVERY ANSWER (MANDATORY):
 - For every user query, quickly probe the RAG store using `rag_retrieval` with 1-3 keywords extracted from the query.
 - If the query is about the user or prior conversations, apply filter_metadata type=user_fact.
 - If the query is general but may benefit from local knowledge, search without filter to find relevant project or local documents.
 - If relevant snippets are found, incorporate them into your answer (you may mention that the info comes from local knowledge).
 - If nothing relevant is found, continue normally; do not fabricate.
 - Do not include curly braces in examples to avoid prompt template variable interpolation issues.
        """.strip()
        
        return self.config.get('system_message', default_message)
    
    # ---------------------
    # Personal memory helpers (generic agent)
    # ---------------------
    def _extract_keywords(self, query: str) -> list:
        """Lightweight keyword extractor for memory-related prompts (EN)."""
        q = (query or "").lower()
        seeds = [
            "name", "surname", "age", "interest", "like", "love", "prefer", "job", "work", "date", "birthday",
            "meeting", "yesterday", "today", "remember", "preference", "hobby", "place", "city", "country",
            "relationship", "boyfriend", "girlfriend", "partner", "reminder",
        ]
        kws = [w for w in seeds if w in q]
        if not kws:
            kws = ["basic_info", "preferences"]
        out, seen = [], set()
        for k in kws:
            if k not in seen:
                out.append(k)
                seen.add(k)
        return out

    def _build_memory_context(self, query: str) -> str:
        """Build a short memory context using the RAG tools if available.
        Strategy:
          - Include compact recent chat history (last few user and assistant messages).
          - For extracted keywords, first retrieve with filter {type:user_fact}; if empty, fallback without filter.
          - Cap total snippets to ~3-5 and total length to ~1200 chars.
        """
        try:
            parts = []

            # 1) Compact recent chat history (last 4 messages)
            try:
                msgs = self.memory.chat_memory.messages if self.memory else []
                if msgs:
                    tail = msgs[-4:]
                    hist_lines = []
                    for m in tail:
                        role = getattr(m, 'type', getattr(m, 'role', ''))
                        content = getattr(m, 'content', '')
                        if not content:
                            continue
                        role_tag = 'U' if 'human' in role or role == 'user' else 'A'
                        snippet = content[:200]
                        snippet = snippet.replace("\n", " ")
                        hist_lines.append(f"{role_tag}: {snippet}")
                    if hist_lines:
                        parts.append("Recent history: " + " | ".join(hist_lines))
            except Exception:
                pass

            # 2) RAG retrieval: filtered first, then fallback
            rr_tool = self.tool_manager.get_tool('rag_retrieval') if hasattr(self, 'tool_manager') else None
            if rr_tool:
                related = []
                for kw in self._extract_keywords(query):
                    found_any = False
                    try:
                        # Filtered by user_fact
                        res_f = rr_tool.func(query=kw, k=3, with_scores=False, filter_metadata={"type":"user_fact"})
                        if isinstance(res_f, str) and 'no documents found' not in res_f.lower():
                            lines = [line for line in res_f.splitlines() if line.strip()]
                            if lines:
                                related.append(f"{kw}: " + "; ".join(lines[1:5] if len(lines) > 1 else lines))
                                found_any = True
                    except Exception:
                        pass
                    if not found_any:
                        try:
                            res_u = rr_tool.func(query=kw, k=2, with_scores=False, filter_metadata=None)
                            if isinstance(res_u, str) and 'no documents found' not in res_u.lower():
                                lines = [line for line in res_u.splitlines() if line.strip()]
                                if lines:
                                    related.append(f"{kw}*: " + "; ".join(lines[1:4] if len(lines) > 1 else lines))
                        except Exception:
                            pass
                if related:
                    # Cap to 3 items to keep context concise
                    parts.append("User facts: " + " | ".join(related[:3]))

            context = "\n".join([p for p in parts if p])
            return context[:1200]
        except Exception:
            return ""

    def _auto_learn_from_user(self, query: str):
        """Lightweight EN-only rule-based extractor to persist obvious self-disclosures via RAG.
        This complements tool-calling in cases when the LLM skips the tool.
        """
        try:
            if not query:
                return
            rm_tool = self.tool_manager.get_tool('rag_management') if hasattr(self, 'tool_manager') else None
            if not rm_tool:
                return
            text = query.strip()
            low = text.lower()

            # Name patterns (EN)
            m = re.search(r"(?:my\s+name\s+is|i'm|im|call\s+me)\s+([A-Za-z\-]+)", text, re.IGNORECASE)
            if m:
                name = m.group(1).strip()
                rm_tool.func(action='add_text', content=f"User name: {name}", metadata={"type":"user_fact","field":"name"})
                return

            # Age patterns (EN)
            m = re.search(r"i\s*am\s*(\d{1,3})\s*years?\s*old\b", low, re.IGNORECASE)
            if not m:
                m = re.search(r"my\s*age\s*is\s*(\d{1,3})\b", low, re.IGNORECASE)
            if m:
                age = m.group(1)
                rm_tool.func(action='add_text', content=f"User age: {age}", metadata={"type":"user_fact","field":"age"})
                return

            # Occupation / job (EN)
            m = re.search(r"(?:i\s*work\s*as|my\s*profession\s*is|i\s*am\s*an?\s+)\s*([^\n\r\.;:,!?]+)", low, re.IGNORECASE)
            if m:
                occ = m.group(1).strip()
                rm_tool.func(action='add_text', content=f"User occupation: {occ}", metadata={"type":"user_fact","field":"occupation"})
                return

            # Location (EN)
            m = re.search(r"(?:i\s*live\s*in|my\s*city\s*is)\s*([^\n\r\.;:,!?]+)", low, re.IGNORECASE)
            if m:
                loc = m.group(1).strip()
                rm_tool.func(action='add_text', content=f"User location: {loc}", metadata={"type":"user_fact","field":"location"})
                return

            # Preferences / likes (EN)
            m = re.search(r"(?:i\s*like|i\s*love)\s+([^\n\r]+)", low, re.IGNORECASE)
            if m:
                pref = m.group(1).strip()
                rm_tool.func(action='add_text', content=f"Likes: {pref}", metadata={"type":"user_fact","field":"preference"})
                return

            # Hobbies / activities (EN)
            m = re.search(r"(?:i\s*play\s*|i\s*do\s*|i\s*am\s*into\s*)\s*([^\n\r]+)", low, re.IGNORECASE)
            if m:
                hobby = m.group(1).strip()
                rm_tool.func(action='add_text', content=f"Hobby/activity: {hobby}", metadata={"type":"user_fact","field":"hobby"})
                return
        except Exception:
            # Silent fail, we don't want to break the main flow
            return

    def _initialize_agent(self):
        """Initialize the LangChain agent."""
        try:
            tools = self.tool_manager.get_tools()
            
            # Create prompt template for tool calling
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_message),
                MessagesPlaceholder("chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad")
            ])
            
            # Bind tools to the LLM
            llm_with_tools = self.llm.bind_tools(tools)

            # Create tool calling agent
            agent = create_tool_calling_agent(
                llm=llm_with_tools,
                tools=tools,
                prompt=prompt
            )
            
            # Create agent executor with proper error handling
            self.agent = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=self.verbose,
                memory=self.memory,
                max_iterations=30,
                handle_parsing_errors=True,
                return_intermediate_steps=False,
                callbacks=[self.callback_handler] if self.verbose else []
            )
            
            self.logger.info(f"Agent initialized with {len(tools)} tools")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agent: {e}")
            raise
    
    def add_tool(self, tool: Tool):
        """Add a tool to the agent."""
        try:
            self.tool_manager.add_tool(tool)
            self._initialize_agent()  # Reinitialize agent with new tools
            self.logger.info(f"Tool added: {tool.name}")
        except Exception as e:
            self.logger.error(f"Failed to add tool {tool.name}: {e}")
            raise
    
    def remove_tool(self, tool_name: str):
        """Remove a tool from the agent."""
        try:
            self.tool_manager.remove_tool(tool_name)
            self._initialize_agent()  # Reinitialize agent without removed tool
            self.logger.info(f"Tool removed: {tool_name}")
        except Exception as e:
            self.logger.error(f"Failed to remove tool {tool_name}: {e}")
            raise
    
    def list_tools(self) -> List[str]:
        """Get list of available tool names."""
        return self.tool_manager.list_tools()
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all available tools."""
        return self.tool_manager.get_tool_descriptions()
    
    def process_query(self, query: str) -> str:
        """
        Run the agent with a query.
        
        Args:
            query: User query/prompt
            
        Returns:
            Agent response
        """
        try:
            self.logger.info(f"Processing query: {query[:50]}...")
            
            # Let the agent decide when to call tools (fact_extractor, rag_management)

            # Build a lightweight memory context via RAG and inject before the query
            try:
                memory_context = self._build_memory_context(query)
            except Exception:
                memory_context = ""

            composed_input = (
                f"[MEMORY CONTEXT]\n{memory_context}\n\n[USER]\n{query}" if memory_context else query
            )

            # Use invoke with composed input
            result = self.agent.invoke({
                "input": composed_input,
                "chat_history": self.memory.chat_memory.messages if self.memory else []
            })
            
            # Log intermediate steps for observation visibility
            if self.verbose and "intermediate_steps" in result:
                for i, (action, observation) in enumerate(result["intermediate_steps"], 1):
                    self.logger.info(f"Step {i} - Action: {action.tool} with input: {action.tool_input}")
                    self.logger.info(f"Step {i} - Observation: {str(observation)[:200]}...")
            
            response = result.get("output", "Error: failed to get a response")
            self.logger.info("Query processed successfully")
            
            return response
        except Exception as e:
            error_msg = f"Error processing query: {e}"
            self.logger.error(error_msg)
            return f"Sorry, an error occurred while processing the request: {e}"

    def _llm_extract_and_store_facts(self, message: str, min_confidence: float = 0.6):
        """Use the registered fact_extractor tool to extract facts and save them into RAG.
        Stores each item via rag_management.add_text with rich metadata.
        """
        try:
            if not message:
                return
            extractor = self.tool_manager.get_tool('fact_extractor') if hasattr(self, 'tool_manager') else None
            rag_mgmt = self.tool_manager.get_tool('rag_management') if hasattr(self, 'tool_manager') else None
            if not extractor or not rag_mgmt:
                return
            raw = extractor.func(message=message)
            items = []
            try:
                items = json.loads(raw) if raw else []
                if not isinstance(items, list):
                    items = []
            except Exception:
                items = []
            saved = 0
            for it in items:
                try:
                    conf = float(it.get('confidence', 0))
                    if conf < min_confidence:
                        continue
                    ftype = (it.get('type') or 'user_fact').strip()
                    field = (it.get('field') or '').strip()
                    value = (it.get('value') or '').strip()
                    relation = (it.get('relation') or '').strip()
                    lang = (it.get('language') or '').strip()
                    if not value:
                        continue
                    # Compose human-readable content
                    label = field if field else ftype
                    if relation:
                        content = f"{label} ({relation}): {value}"
                    else:
                        content = f"{label}: {value}"
                    # Metadata for RAG filtering
                    meta = {
                        "type": "user_fact",
                        "field": field or ftype,
                        "relation": relation or None,
                        "source": "chat",
                        "language": lang or None,
                        "confidence": conf,
                    }
                    # Remove None values
                    meta = {k: v for k, v in meta.items() if v is not None}
                    rag_mgmt.func(action='add_text', content=content, metadata=meta)
                    saved += 1
                except Exception:
                    continue
            if saved:
                self.logger.info(f"LLM fact extractor saved {saved} item(s) to RAG")
        except Exception as e:
            self.logger.debug(f"_llm_extract_and_store_facts error: {e}")
    
    def run(self, query: str) -> str:
        """Backward-compatible alias for process_query()."""
        return self.process_query(query)
    
    def reset_memory(self):
        """Reset conversation memory."""
        self.memory.clear()
        self.logger.info("Memory reset")
    
    def get_memory(self) -> List[Dict]:
        """Get conversation history."""
        return self.memory.chat_memory.messages
