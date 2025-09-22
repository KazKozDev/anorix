#!/usr/bin/env python3
"""
Enhanced interactive shell with full memory support.
Remembers conversations between sessions.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional

from agent import OllamaAgent


class EnhancedInteractiveAgent:
    """Enhanced interactive shell with memory persistence."""

    def __init__(self, model_name: str = "gpt-oss:20b", verbose: bool = True, continue_session: bool = True):
        """
        Initialize the enhanced interactive agent.

        Args:
            model_name: Ollama model name
            verbose: Verbose output
            continue_session: Whether to continue last session or start new
        """
        self.model_name = model_name
        self.verbose = verbose
        self.continue_session = continue_session
        self.agent = None
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize the agent with memory."""
        print("🧠 Initializing Enhanced AI Agent with Memory...")
        print(f"Model: {self.model_name}")

        try:
            self.agent = OllamaAgent(
                model_name=self.model_name,
                temperature=0.1,
                verbose=self.verbose,
                memory_config_path="config/memory_config.yaml"
            )

            # Check memory system
            if self.agent.memory_manager:
                print("✅ Memory system active")

                # Show memory stats
                stats = self.agent.get_memory_stats()
                print(f"📊 Memory: {stats['long_term']['conversations_count']} conversations, {stats['long_term']['facts_count']} facts")

                # Continue last session or start new
                if self.continue_session:
                    session_id = self.agent.continue_last_session()
                    print(f"🔄 Continuing session: {session_id[:8]}...")
                else:
                    session_id = self.agent.start_new_session()
                    print(f"🆕 New session: {session_id[:8]}...")

                # Show user context if available
                self._show_user_context()

            else:
                print("⚠️ Memory system not available")

            # Show available tools
            tools = self.agent.list_tools()
            memory_tools = [tool for tool in tools if any(mem in tool for mem in ['memory', 'profile', 'facts', 'conversation'])]

            if memory_tools:
                print(f"🔧 Memory tools: {', '.join(memory_tools)}")

            print(f"🔧 Total tools: {len(tools)}")
            print("=" * 60)

        except Exception as e:
            print(f"❌ Failed to initialize agent: {e}")
            raise

    def _show_user_context(self):
        """Show current user context."""
        if not self.agent.memory_manager:
            return

        try:
            # Show user profile
            profile = self.agent.get_user_profile()
            if profile and any(key != 'test_key' for key in profile.keys()):
                print("\n👤 Your profile:")
                for key, value in profile.items():
                    if key != 'test_key':  # Skip test data
                        print(f"   {key}: {value}")

            # Show recent facts
            facts = self.agent.get_facts()
            relevant_facts = [f for f in facts if f.get('category') != 'testing'][:3]
            if relevant_facts:
                print("\n📝 What I remember about you:")
                for fact in relevant_facts:
                    category = fact.get('category', '')
                    content = fact.get('fact', '')[:60]
                    print(f"   [{category}] {content}...")

        except Exception as e:
            print(f"⚠️ Could not load context: {e}")

    def run_interactive(self):
        """Run the interactive shell."""
        print("🤖 Enhanced AI Assistant Ready!")
        print("💡 I can remember our conversations and learn about you over time.")
        print("Type 'help' for commands, 'quit' to exit, or just start chatting!")
        print("-" * 60)

        while True:
            try:
                user_input = input("\n💬 You: ").strip()

                if not user_input:
                    continue

                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    self._handle_exit()
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                elif user_input.lower() == 'memory':
                    self._show_memory_info()
                    continue
                elif user_input.lower() == 'profile':
                    self._show_profile()
                    continue
                elif user_input.lower().startswith('search '):
                    query = user_input[7:]
                    self._search_memory(query)
                    continue
                elif user_input.lower() == 'clear':
                    os.system('clear' if os.name == 'posix' else 'cls')
                    continue
                elif user_input.lower() == 'new_session':
                    self._start_new_session()
                    continue

                # Process with agent
                print("\n🤖 Assistant: ", end="", flush=True)
                response = self.agent.run(user_input)
                print(response)

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("💡 Try typing 'help' for assistance.")

    def _handle_exit(self):
        """Handle exit gracefully."""
        if self.agent and self.agent.memory_manager:
            stats = self.agent.get_memory_stats()
            conv_count = stats['long_term']['conversations_count']
            facts_count = stats['long_term']['facts_count']

            print(f"\n💾 Session saved! Total: {conv_count} conversations, {facts_count} facts")
            print("🧠 I'll remember our conversation for next time!")

        print("👋 Goodbye! See you next time!")

    def _show_help(self):
        """Show help information."""
        print("\n📚 Enhanced AI Assistant Commands:")
        print("=" * 40)
        print("🗣️  Just type anything - I'll remember our conversation!")
        print("📋 help          - Show this help")
        print("🧠 memory        - Show memory statistics")
        print("👤 profile       - Show your profile")
        print("🔍 search <text> - Search past conversations")
        print("🆕 new_session   - Start a fresh session")
        print("🧹 clear         - Clear screen")
        print("🚪 quit/exit     - End conversation")
        print("\n💡 I can also:")
        print("   • Remember facts about you")
        print("   • Continue conversations from where we left off")
        print("   • Search through our chat history")
        print("   • Learn your preferences over time")

    def _show_memory_info(self):
        """Show memory statistics."""
        if not self.agent or not self.agent.memory_manager:
            print("⚠️ Memory system not available")
            return

        try:
            stats = self.agent.get_memory_stats()

            print("\n🧠 Memory System Status:")
            print("=" * 30)

            # Short-term memory
            short_term = stats.get('short_term', {})
            print(f"📋 Active conversation: {short_term.get('current_messages', 0)}/{short_term.get('max_messages', 0)} messages")

            # Long-term memory
            long_term = stats.get('long_term', {})
            print(f"💾 Total conversations: {long_term.get('conversations_count', 0)}")
            print(f"📝 Stored facts: {long_term.get('facts_count', 0)}")
            print(f"💽 Database size: {long_term.get('database_size_mb', 0)} MB")

            # Smart memory
            smart_memory = stats.get('smart_memory', {})
            if 'total_documents' in smart_memory:
                print(f"🔍 Searchable documents: {smart_memory.get('total_documents', 0)}")
                print(f"🧮 Vector DB size: {smart_memory.get('storage_size_mb', 0)} MB")

            # Session info
            session_id = self.agent.memory_manager.get_current_session_id()
            print(f"🆔 Current session: {session_id[:8]}...")

        except Exception as e:
            print(f"❌ Error getting memory stats: {e}")

    def _show_profile(self):
        """Show user profile."""
        if not self.agent:
            print("⚠️ Agent not available")
            return

        try:
            profile = self.agent.get_user_profile()

            if not profile or all(key == 'test_key' for key in profile.keys()):
                print("\n👤 No profile information yet.")
                print("💡 Start chatting and I'll learn about you!")
                return

            print("\n👤 Your Profile:")
            print("=" * 20)
            for key, value in profile.items():
                if key != 'test_key':  # Skip test data
                    print(f"   {key.replace('_', ' ').title()}: {value}")

        except Exception as e:
            print(f"❌ Error getting profile: {e}")

    def _search_memory(self, query: str):
        """Search through memory."""
        if not self.agent or not self.agent.memory_manager:
            print("⚠️ Memory system not available")
            return

        try:
            results = self.agent.search_memories(query, method="both", limit=5)

            if not results:
                print(f"🔍 No results found for '{query}'")
                return

            print(f"\n🔍 Search results for '{query}':")
            print("=" * 40)

            for i, result in enumerate(results, 1):
                content = result.get('content', '')[:80]
                similarity = result.get('similarity', 0)
                method = result.get('search_method', 'unknown')

                print(f"{i}. {content}...")
                print(f"   📊 Relevance: {similarity:.1%} ({method})")
                print()

        except Exception as e:
            print(f"❌ Search error: {e}")

    def _start_new_session(self):
        """Start a new conversation session."""
        if not self.agent or not self.agent.memory_manager:
            print("⚠️ Memory system not available")
            return

        try:
            session_id = self.agent.start_new_session()
            print(f"🆕 Started new session: {session_id[:8]}...")
            print("🧹 Conversation context cleared, but I still remember you!")

        except Exception as e:
            print(f"❌ Error starting new session: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Enhanced Interactive AI Agent with Memory")
    parser.add_argument("--model", default="gpt-oss:20b", help="Ollama model name")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--new-session", action="store_true", help="Start new session instead of continuing")

    args = parser.parse_args()

    try:
        interactive_agent = EnhancedInteractiveAgent(
            model_name=args.model,
            verbose=args.verbose,
            continue_session=not args.new_session
        )
        interactive_agent.run_interactive()

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()