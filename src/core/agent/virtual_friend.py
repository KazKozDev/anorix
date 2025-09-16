"""
Virtual Friend - Enhanced agent with personality, memory, and emotional intelligence.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .core import OllamaAgent
from .tools.emotional_intelligence import EmotionalIntelligenceTool
from .tools.personality_system import PersonalitySystem
from .tools.proactive_care import ProactiveCare


class VirtualFriend(OllamaAgent):
    """
    Enhanced agent that acts as a virtual friend with personality, memory, and emotional intelligence.
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,  # Slightly higher can be set via settings
        config_path: Optional[str] = None,
        friend_name: str = "Anorix",
        verbose: bool = False
    ):
        """
        Initialize Virtual Friend.
        
        Args:
            model_name: Name of the Ollama model to use
            base_url: Ollama server URL
            temperature: LLM temperature setting
            config_path: Path to configuration file
            verbose: Enable verbose logging
            friend_name: Name of the virtual friend
        """
        # Initialize parent class
        super().__init__(model_name, base_url, temperature, config_path, verbose)
        
        self.friend_name = friend_name
        
        # Initialize friend-specific tools (memory via RAG)
        self.emotional_intelligence = EmotionalIntelligenceTool()
        self.personality_system = PersonalitySystem()
        self.proactive_care = ProactiveCare()
        
        # Enhanced system message for virtual friend
        self.friend_system_message = self._get_friend_system_message()
        
        # Override system message
        self.system_message = self.friend_system_message
        
        # Reinitialize agent with new system message
        self._initialize_agent()
        
        self.logger.info(f"Virtual Friend '{friend_name}' initialized successfully")
    
    def _get_friend_system_message(self) -> str:
        """Get enhanced system message for virtual friend."""
        personality_info = self.personality_system.personality_data
        friend_info = personality_info["friend_info"]
        
        base_message = f"""
You are {friend_info['name']} — {friend_info['personality_type']}. Your role is to be a genuine virtual friend to the user.

YOUR PERSONALITY:
{friend_info['backstory']}

CORE PRINCIPLES:
1) MEMORY — Always use RAG (rag_management/rag_retrieval) to remember and retrieve facts about the user. For new self-disclosures, first analyze with the fact_extractor tool (see TOOLS) using context, then save confirmed facts to RAG.
2) EMOTIONS — Analyze the user's mood via emotional_intelligence and respond accordingly.
3) ADAPTATION — Use personality_system to adapt your communication style.
4) CARE — Provide proactive_care through reminders and support.
5) EVOLUTION — Grow and change based on interactions with the user.

COMMUNICATION STYLE:
- Speak naturally and friendly.
- Use emojis to convey emotions when suitable.
- Ask questions and show sincere interest.
- Remember details and refer to them in future conversations.
- Offer emotional support.
- Answer in the user's language (English/Russian) based on their messages.

MANDATORY STEPS IN EVERY CONVERSATION:
1) ALWAYS FIRST attempt to retrieve user facts via RAG (rag_retrieval) using keywords from the query (name, age, preferences, job, dates, places, relationships, events) with metadata filter type=user_fact.
   - Use retrieved facts to personalize your answer.
2) Analyze the user's emotional state via emotional_intelligence.
3) When the user shares new information, call fact_extractor with:
   - message: the current user message
   - context: a compact window (recent chat history summary + 3-5 relevant RAG snippets)
   Extract only explicitly stated facts (do not infer). For critical fields (name, age, relationships, address) ask a brief confirmation before saving via rag_management add_text.
4) Save only high-confidence, non-conflicting facts to RAG (type=user_fact) with structured metadata (field, relation if applicable, source, language, confidence). If conflicting with existing data, ask a clarifying question.
5) Adapt your behavior to the user's current mood.
6) Use accumulated knowledge to personalize every answer.

CRITICAL:
- NEVER say "I don't know" to questions about the user WITHOUT first attempting RAG retrieval.
- FIRST try rag_retrieval (with filter type=user_fact).
  - Only if nothing is truly found, say you don't have that information and politely invite them to share it so you can remember (via rag_management add_text).
  - Use any retrieved information to personalize your answer.

TOOLS:
- fact_extractor: extract structured facts from a message using provided context (recent chat history summary + relevant RAG snippets). Return a JSON array. Do not invent facts. Use only what is explicitly stated.
- rag_management / rag_retrieval: store (add_text) and retrieve user facts.
- emotional_intelligence: analyze mood and provide emotional support.
- personality_system: manage personality and communication style.
- proactive_care: reminders, care, and support.
- All standard tools for search, files, and calculation.

REQUEST HANDLING ALGORITHM:
- If the user asks about themself/their life → rag_retrieval with relevant keywords (filter type=user_fact).
- If the user shares new information → call fact_extractor (with context), then for confirmed items save via rag_management add_text (type=user_fact) with structured metadata.
- If the user expresses emotions → emotional_intelligence analyze_mood.
- ALWAYS use found information to personalize your response.

STRICT MEMORY CHECK BEFORE ANY ANSWER:
1) Try rag_retrieval using keywords from the query with filter type=user_fact.
2) Match retrieved facts to the question and select the relevant ones.
3) Construct the reply referencing those facts (explicitly or implicitly) so the user feels personalization.
4) If no facts exist, say neutrally that you don't have that info yet and offer to remember it if they share.

EXAMPLES OF BEHAVIOR:

BAD ❌:
User: "What is my name?"
Answer: "I don't know your name."

GOOD ✅:
User: "What is my name?"
1) Run rag_retrieval with query "name" and filter type=user_fact.
2) Find the user's name.
3) Answer: "Your name is [name]! 😊"

BAD ❌:
User: "What do I like?"
Answer: "Tell me about your preferences."

GOOD ✅:
User: "What do I like?"
1) Run rag_retrieval with query "like/love/preferences" (filter type=user_fact).
2) Review matching snippets.
3) Answer: "I remember you like [preference list]."

ALWAYS use memory BEFORE answering questions about the user.

CHECKLIST BEFORE ANSWERING (SELF-CHECK):
- [ ] Ran rag_retrieval on keywords from the request (type=user_fact).
- [ ] Used relevant facts in the answer.
- [ ] Offered to save new important information when it appeared.

Remember: you are not just an assistant — you are a true friend who grows and evolves with the user!
        """.strip()
        
        return base_message
    
    def process_query(self, query: str) -> str:
        """
        Enhanced query processing with friend-specific behaviors.
        
        Args:
            query: User query/prompt
            
        Returns:
            Friend response
        """
        try:
            # Pre-processing: analyze emotions (stats update skipped)
            self._pre_process_interaction(query)

            # Process with parent method using the raw user input (no awareness context)
            response = super().process_query(query)
            
            # Post-processing: learn and adapt
            self._post_process_interaction(query, response)
            
            return response
            
        except Exception as e:
            error_msg = f"Error processing query: {e}"
            self.logger.error(error_msg)
            return f"Sorry, an error occurred: {e}"
    
    def _pre_process_interaction(self, query: str):
        """Pre-process user interaction."""
        try:
            # Update interaction stats (through RAG we don't have counters; skip)
            
            # Analyze emotions in the query
            emotion_analysis = self.emotional_intelligence._analyze_mood(query)
            if ("mood:" in emotion_analysis.lower()):
                self.logger.info(f"Detected emotion in user input: {emotion_analysis}")
            
            # Check if query requires memory context and inject hint
            memory_triggers = [
                "what is my name", "my name", "who am i",
                "what do i like", "my interests", "my preferences",
                "where do i work", "my job", "my profession",
                "how old am i", "my age", "my birthday",
                "what did i tell", "do you remember", "what do you know about me"
            ]
            
            query_lower = query.lower()
            if any(trigger in query_lower for trigger in memory_triggers):
                self.logger.info(f"Query requires memory context: {query[:50]}...")
                # This will be picked up by the system prompt
                
        except Exception as e:
            self.logger.warning(f"Error in pre-processing: {e}")
    
    def _post_process_interaction(self, query: str, response: str):
        """Post-process interaction for learning."""
        try:
            # Adapt personality based on interaction
            if self.personality_system.should_evolve():
                self.personality_system._adapt_to_user(query)
            
            # Check for proactive care opportunities
            if self.proactive_care.should_check_in():
                self.logger.info("User might benefit from proactive check-in")
            
        except Exception as e:
            self.logger.warning(f"Error in post-processing: {e}")

    def _extract_keywords(self, query: str) -> list[str]:
        """Very lightweight keyword extractor for Russian/English prompts."""
        q = (query or "").lower()
        seeds = [
            "name", "surname", "age", "like", "love", "prefer", "job", "work", "birthday", "reminder",
        ]
        kws = [w for w in seeds if w in q]
        # Always include a couple of generic probes if none matched
        if not kws:
            kws = ["basic_info", "preferences"]
        # Deduplicate keeping order
        out, seen = [], set()
        for k in kws:
            if k not in seen:
                out.append(k)
                seen.add(k)
        return out
    
    def get_friend_status(self) -> str:
        """Get comprehensive status of the virtual friend."""
        status_parts = []
        
        # Friend info
        personality_data = self.personality_system.personality_data
        friend_info = personality_data["friend_info"]
        status_parts.append(f"🤖 Friend: {friend_info['name']}")
        status_parts.append(f"✨ Personality: {friend_info['personality_type']}")
        
        # RAG memory stats
        try:
            if hasattr(self, 'tool_manager') and getattr(self.tool_manager, 'rag_tool', None):
                info = self.tool_manager.rag_tool.get_collection_info()
                doc_count = info.get('document_count', 'N/A') if isinstance(info, dict) else 'N/A'
                status_parts.append(f"🧠 Knowledge base records (RAG): {doc_count}")
            else:
                status_parts.append("🧠 Knowledge base (RAG): unavailable")
        except Exception:
            status_parts.append("🧠 Knowledge base (RAG): access error")
        
        # Emotional state
        try:
            emotion_data = self.emotional_intelligence.emotion_data
            recent_moods = self.emotional_intelligence._get_recent_moods(days=3)
            status_parts.append(f"💭 Mood records (3 days): {len(recent_moods)}")
        except:
            status_parts.append("💭 Emotional data: unavailable")
        
        # Care status
        try:
            active_reminders = [r for r in self.proactive_care.care_data["reminders"] if r["active"]]
            status_parts.append(f"⏰ Active reminders: {len(active_reminders)}")
        except:
            status_parts.append("⏰ Care system: unavailable")
        
        # Personality traits (top 3)
        try:
            traits = personality_data["core_traits"]
            top_traits = sorted(traits.items(), key=lambda x: x[1], reverse=True)[:3]
            trait_str = ", ".join([f"{t[0]}: {t[1]}/10" for t in top_traits])
            status_parts.append(f"🎭 Top traits: {trait_str}")
        except:
            status_parts.append("🎭 Personality data: unavailable")
        
        return "\n".join(status_parts)
    
    def proactive_check_in(self) -> Optional[str]:
        """Perform proactive check-in if needed."""
        try:
            if self.proactive_care.should_check_in():
                return self.proactive_care._proactive_check_in()
            else:
                return None
        except Exception as e:
            self.logger.error(f"Error in proactive check-in: {e}")
            return None
    
    def get_pending_reminders(self) -> list:
        """Get any pending reminders."""
        try:
            return self.proactive_care.check_pending_reminders()
        except Exception as e:
            self.logger.error(f"Error getting pending reminders: {e}")
            return []
    
    def remember_about_user(self, content: str, category: str = "fact", importance: int = 5):
        """Directly remember something about the user via RAG."""
        try:
            rm_tool = self.tool_manager.get_tool('rag_management') if hasattr(self, 'tool_manager') else None
            if not rm_tool:
                return "RAG management tool is not available"
            meta = {"type": "user_fact", "category": category, "importance": importance, "source": "virtual_friend"}
            return rm_tool.func(action='add_text', content=content, metadata=meta)
        except Exception as e:
            self.logger.error(f"Error remembering about user: {e}")
            return f"Failed to remember: {e}"
    
    def analyze_user_mood(self, text: str) -> str:
        """Directly analyze user's mood from text."""
        try:
            return self.emotional_intelligence._analyze_mood(text)
        except Exception as e:
            self.logger.error(f"Error analyzing mood: {e}")
            return "Failed to analyze mood"
    
    def adapt_personality(self, context: str) -> str:
        """Directly adapt personality based on context."""
        try:
            return self.personality_system._adapt_to_user(context)
        except Exception as e:
            self.logger.error(f"Error adapting personality: {e}")
            return f"Failed to adapt: {e}"