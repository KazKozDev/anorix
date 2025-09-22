"""
Core agent implementation with Ollama LLM integration.
"""

import logging
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain_ollama.chat_models import ChatOllama as Ollama
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory

from .tool_manager import ToolManager
from .callbacks import DetailedAgentCallbackHandler, SimpleObservationHandler
from .memory.memory_manager import MemoryManager


class OllamaAgent:
    """
    Main agent class with Ollama LLM integration and tool calling capabilities.
    """
    
    def __init__(
        self,
        model_name: str = "gpt-oss:20b",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.1,
        config_path: Optional[str] = None,
        memory_config_path: Optional[str] = None,
        verbose: bool = True
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
        self.memory_config = self._load_config(memory_config_path or "config/memory_config.yaml")
        
        # Override with provided parameters
        self.model_name = model_name or self.config.get('model_name', 'gpt-oss:20b')
        self.base_url = base_url or self.config.get('base_url', 'http://localhost:11434')
        self.temperature = temperature or self.config.get('temperature', 0.1)
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Initialize memory system
        self.memory_manager = self._initialize_memory_system()

        # Initialize tool manager with RAG and memory support
        self.tool_manager = ToolManager(enable_rag=True, memory_manager=self.memory_manager)

        # Initialize LangChain memory (for backward compatibility)
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

        # Load context from previous sessions if enabled
        self._load_session_context()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)

        # Remove existing handlers to prevent duplicate logs
        for h in list(logger.handlers):
            logger.removeHandler(h)

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

    def _initialize_memory_system(self) -> Optional[MemoryManager]:
        """Initialize the three-layer memory system."""
        try:
            if not self.memory_config.get('memory', {}).get('enabled', True):
                self.logger.info("Memory system disabled in configuration")
                return None

            memory_config = self.memory_config.get('memory', {})

            # Get configuration values
            short_term_config = memory_config.get('short_term', {})
            long_term_config = memory_config.get('long_term', {})
            smart_memory_config = memory_config.get('smart_memory', {})

            # Initialize memory manager
            memory_manager = MemoryManager(
                short_term_max_messages=short_term_config.get('max_messages', 10),
                long_term_db_path=long_term_config.get('db_path', 'data/conversations.db'),
                smart_memory_db_path=smart_memory_config.get('db_path', 'data/vector_db'),
                smart_memory_collection=smart_memory_config.get('collection_name', 'conversations'),
                embedding_model=smart_memory_config.get('embedding_model', 'sentence-transformers/all-MiniLM-L6-v2')
            )

            self.logger.info("Memory system initialized successfully")
            return memory_manager

        except Exception as e:
            self.logger.error(f"Failed to initialize memory system: {e}")
            self.logger.info("Continuing without memory system")
            return None

    def _load_session_context(self) -> None:
        """Load context from previous sessions into short-term memory."""
        if not self.memory_manager:
            return

        try:
            memory_config = self.memory_config.get('memory', {})
            short_term_config = memory_config.get('short_term', {})

            # Check if auto-context loading is enabled
            if not short_term_config.get('auto_context', True):
                return

            # Get recent conversations from long-term memory
            recent_limit = short_term_config.get('context_load_limit', 5)
            recent_conversations = self.memory_manager.get_conversation_history(
                days=7,  # Last week
                limit=recent_limit
            )

            if recent_conversations:
                self.logger.info(f"Loading {len(recent_conversations)} recent messages into context")

                # Add recent conversations to short-term memory
                for conv in reversed(recent_conversations):  # Add in chronological order
                    role = conv.get('role', 'user')
                    content = conv.get('content', '')
                    timestamp = conv.get('timestamp', '')

                    # Add to short-term memory with timestamp info
                    self.memory_manager.short_term.add_message(
                        role=role,
                        content=content,
                        metadata={'loaded_from_history': True, 'original_timestamp': timestamp}
                    )

                self.logger.info("Session context loaded successfully")

        except Exception as e:
            self.logger.error(f"Failed to load session context: {e}")

    def _get_user_context_summary(self) -> str:
        """Get a summary of user context for better continuity."""
        if not self.memory_manager:
            return ""

        try:
            # Get user profile
            profile = self.memory_manager.get_user_profile()

            # Get recent facts
            recent_facts = self.memory_manager.get_facts()[:5]  # Top 5 facts

            context_parts = []

            # Add profile info
            if profile:
                profile_info = []
                for key, value in profile.items():
                    if key != 'test_key':  # Skip test data
                        profile_info.append(f"{key}: {value}")

                if profile_info:
                    context_parts.append(f"User profile: {', '.join(profile_info)}")

            # Add key facts
            if recent_facts:
                facts_info = []
                for fact in recent_facts:
                    category = fact.get('category', '')
                    content = fact.get('fact', '')[:50]
                    if category and content and category != 'testing':  # Skip test data
                        facts_info.append(f"[{category}] {content}")

                if facts_info:
                    context_parts.append(f"Key facts: {'; '.join(facts_info)}")

            return ". ".join(context_parts) if context_parts else ""

        except Exception as e:
            self.logger.error(f"Failed to get user context: {e}")
            return ""
    
    def _get_system_message(self) -> str:
        """Get system message for the agent."""
        memory_tools_info = ""
        if self.memory_manager:
            memory_tools_info = """

MEMORY TOOLS:
- memory_search: Search through past conversations using semantic or text search
- profile_tool: Manage user profile information and preferences
- facts_save: Save and retrieve important facts and knowledge
- conversation_history: View conversation history from specific time periods
- calendar: Manage calendar events, appointments, and scheduling
- calendar_nl: Natural language interface for calendar tasks (create, list, search, get, delete)
"""

        # Get user context summary
        user_context = self._get_user_context_summary()
        context_info = ""
        if user_context:
            context_info = f"""

CURRENT USER CONTEXT:
{user_context}

Remember this context when responding to the user. Reference their profile and previous conversations naturally.
"""

        default_message = f"""
You are a helpful AI assistant with access to various tools including advanced memory capabilities.
Use the available tools to accomplish the user's tasks.
Always explain which tool you are using and why.
If the required information is not available, say so honestly.
Respond in the user's language; if the user writes in Russian, respond in Russian.

TOOLING RULES:
- For downloading binary files (e.g., PDFs), use the `http_download` tool. Do NOT use the web scraper or web_search for direct PDF URLs.
- For saving local files, prefer the structured `file_write` tool (args: path, content). Do NOT embed large JSON inside string commands.
- For RAG ingestion, use `rag_management` (actions: add_text, add_file, add_directory). Avoid inventing abstracts; fetch abstracts from authoritative sources (e.g., arXiv abs pages) or cite the source.
- Avoid running `web_search` on a direct URL. If a direct URL is given, act directly (download or open) instead of searching it.{memory_tools_info}

MEMORY AND CALENDAR GUIDELINES:
- When user shares personal information (name, location, profession, age, etc.), use profile_tool to update their profile
- Use memory_search to find relevant past conversations when needed
- Save important facts and information using facts_save
- Reference conversation history when relevant to provide context
 - For calendar-related queries (scheduling, appointments, events), prefer the natural language tool `calendar_nl` to interpret free-form requests.
   Examples:
   - "Создай встречу завтра в 10:00 на 1 час в Zoom" -> calendar_nl
   - "What do I have today?" -> calendar_nl
   - "Search for 'meeting'" -> calendar_nl
   If the request is already structured or you need precise control, you may use the structured `calendar` tool with commands like 'create:title|description|start|end|location'.
- Example: If user says "I live in Moscow", use profile_tool with action="update", key="city", value="Moscow"
- Example: If user says "My name is John", use profile_tool with action="update", key="name", value="John"
 - Example: If user wants to "create a meeting tomorrow at 10 AM", use calendar_nl (it will compute exact times and duration)
 - Example: If user asks "what appointments do I have", use calendar_nl (it will list from the persistent store){context_info}
        """.strip()

        return self.config.get('system_message', default_message)
    
    def _initialize_agent(self):
        # ... (rest of the code remains the same)
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

            # For older versions of LangChain, we need to handle tools differently
            try:
                # Try the new approach with bind_tools
                llm_with_tools = self.llm.bind_tools(tools)
                self.logger.info("Using bind_tools approach for LLM integration")
            except Exception as e:
                self.logger.warning(f"bind_tools not supported: {e}")
                # Fallback: use the LLM as is and let the agent handle tool calling
                llm_with_tools = self.llm
                self.logger.info("Using fallback LLM approach without bind_tools")

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

            # Add user message to memory system
            if self.memory_manager:
                self.memory_manager.add_message("user", query)

            # Use invoke method with proper input format
            result = self.agent.invoke({
                "input": query,
                "chat_history": self.memory.chat_memory.messages if self.memory else []
            })

            # Log intermediate steps for observation visibility
            if self.verbose and "intermediate_steps" in result:
                for i, (action, observation) in enumerate(result["intermediate_steps"], 1):
                    self.logger.info(f"Step {i} - Action: {action.tool} with input: {action.tool_input}")
                    self.logger.info(f"Step {i} - Observation: {str(observation)[:200]}...")

            response = result.get("output", "Error: failed to get a response")

            # Add assistant response to memory system
            if self.memory_manager:
                self.memory_manager.add_message("assistant", response)

            self.logger.info("Query processed successfully")

            return response
        except Exception as e:
            error_msg = f"Error processing query: {e}"
            self.logger.error(error_msg)
            return f"Sorry, an error occurred while processing the request: {e}"
    
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

    # Memory system methods
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        if self.memory_manager:
            return self.memory_manager.get_memory_stats()
        return {"error": "Memory system not available"}

    def start_new_session(self) -> str:
        """Start a new conversation session."""
        if self.memory_manager:
            session_id = self.memory_manager.start_new_session()
            self.reset_memory()  # Also reset LangChain memory
            self._load_session_context()  # Reload context for new session
            return session_id
        return "Memory system not available"

    def continue_last_session(self) -> str:
        """Continue the last conversation session instead of starting new one."""
        if not self.memory_manager:
            return "Memory system not available"

        try:
            # Get the most recent session
            recent_conversations = self.memory_manager.get_conversation_history(limit=1)
            if recent_conversations:
                last_session_id = recent_conversations[0].get('session_id')
                if last_session_id:
                    # Set current session to the last one
                    self.memory_manager.session_id = last_session_id
                    self.logger.info(f"Continuing session: {last_session_id[:8]}...")

                    # Load full context from this session
                    session_conversations = self.memory_manager.get_conversation_history(
                        session_id=last_session_id,
                        limit=10
                    )

                    # Clear short-term memory and reload with session context
                    self.memory_manager.short_term.clear()
                    for conv in reversed(session_conversations):
                        self.memory_manager.short_term.add_message(
                            role=conv.get('role', 'user'),
                            content=conv.get('content', ''),
                            metadata={'continued_session': True}
                        )

                    return last_session_id

            # If no previous session, start new one
            return self.start_new_session()

        except Exception as e:
            self.logger.error(f"Failed to continue last session: {e}")
            return self.start_new_session()

    def search_memories(self, query: str, method: str = "semantic", limit: int = 5) -> List[Dict[str, Any]]:
        """Search through conversation history."""
        if self.memory_manager:
            return self.memory_manager.search_memories(query, method, limit)
        return []

    def get_user_profile(self) -> Dict[str, Any]:
        """Get user profile information."""
        if self.memory_manager:
            return self.memory_manager.get_user_profile()
        return {}

    def update_user_profile(self, key: str, value: Any) -> bool:
        """Update user profile."""
        if self.memory_manager:
            return self.memory_manager.update_user_profile(key, value)
        return False

    def save_fact(self, category: str, fact: str, source: str = None, confidence: float = 1.0) -> bool:
        """Save a fact to memory."""
        if self.memory_manager:
            return self.memory_manager.save_fact(category, fact, source, confidence)
        return False

    def get_facts(self, category: str = None, min_confidence: float = 0.0) -> List[Dict[str, Any]]:
        """Get facts from memory."""
        if self.memory_manager:
            return self.memory_manager.get_facts(category, min_confidence)
        return []