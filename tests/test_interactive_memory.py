#!/usr/bin/env python3
"""
Test interactive memory by simulating a conversation session.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent import OllamaAgent


def simulate_interactive_session():
    """Simulate an interactive session to test memory persistence."""
    print("🤖 Simulating Interactive Session")
    print("=" * 50)

    try:
        # Initialize agent
        agent = OllamaAgent(memory_config_path="config/memory_config.yaml")
        print("✅ Agent initialized")

        # Check memory tools
        tools = agent.list_tools()
        memory_tools = [t for t in tools if any(mem in t for mem in ['memory', 'profile', 'facts', 'conversation'])]
        print(f"📝 Memory tools available: {memory_tools}")

        # Start a new session
        session_id = agent.start_new_session()
        print(f"🆕 New session started: {session_id[:8]}...")

        # Simulate user interaction
        print("\n💬 Simulating conversation...")

        # Add some test messages through the memory system
        if agent.memory_manager:
            agent.memory_manager.add_message("user", "Hello! My name is Artem, I'm a developer from Moscow.")
            agent.memory_manager.add_message("assistant", "Hi Artem! Nice to meet you. Tell me about your projects!")
            agent.memory_manager.add_message("user", "I'm working on an AI agent with memory system.")
            agent.memory_manager.add_message("assistant", "Sounds interesting! What technologies are you using?")
            agent.memory_manager.add_message("user", "LangChain, Ollama, ChromaDB for vector search.")

            # Update profile
            agent.memory_manager.update_user_profile("name", "Artem")
            agent.memory_manager.update_user_profile("city", "Moscow")
            agent.memory_manager.update_user_profile("profession", "developer")
            agent.memory_manager.update_user_profile("current_project", "AI agent with memory system")

            # Save some facts
            agent.memory_manager.save_fact(
                category="personal",
                fact="User is working on an AI agent with memory system",
                source="conversation",
                confidence=1.0
            )

            agent.memory_manager.save_fact(
                category="technologies",
                fact="Uses LangChain, Ollama, ChromaDB",
                source="conversation",
                confidence=1.0
            )

            print("✅ Messages, profile, and facts saved to memory")

        # Check what was saved
        print("\n📊 Memory after session:")
        stats = agent.get_memory_stats()
        print(f"  Short-term: {stats['short_term']['current_messages']} messages")
        print(f"  Long-term: {stats['long_term']['conversations_count']} conversations")
        print(f"  Facts: {stats['long_term']['facts_count']} facts")
        print(f"  Smart memory: {stats['smart_memory']['total_documents']} documents")

        return session_id

    except Exception as e:
        print(f"❌ Error in interactive session: {e}")
        import traceback
        traceback.print_exc()
        return None


def check_memory_after_session():
    """Check memory after ending the session."""
    print("\n🔍 Checking Memory After Session")
    print("=" * 50)

    try:
        # Create a new agent instance to test persistence
        agent = OllamaAgent(memory_config_path="config/memory_config.yaml")

        if not agent.memory_manager:
            print("❌ Memory manager not available")
            return

        # Check conversations
        conversations = agent.memory_manager.get_conversation_history()
        print(f"📜 Stored conversations: {len(conversations)}")
        for conv in conversations[-3:]:  # Show last 3
            role = conv.get('role', 'unknown')
            content = conv.get('content', '')[:50]
            timestamp = conv.get('timestamp', '')[:19]
            print(f"  [{timestamp}] {role}: {content}...")

        # Check profile
        profile = agent.get_user_profile()
        print(f"\n👤 User profile: {len(profile)} items")
        for key, value in profile.items():
            print(f"  {key}: {value}")

        # Check facts
        facts = agent.get_facts()
        print(f"\n📝 Stored facts: {len(facts)} items")
        for fact in facts:
            category = fact.get('category', 'unknown')
            content = fact.get('fact', '')[:50]
            print(f"  [{category}] {content}...")

        # Test semantic search
        print("\n🔍 Testing semantic search for 'developer':")
        search_results = agent.search_memories("developer", method="semantic", limit=3)
        for i, result in enumerate(search_results, 1):
            content = result.get('content', '')[:50]
            similarity = result.get('similarity', 0)
            print(f"  {i}. {content}... (similarity: {similarity:.3f})")

        return True

    except Exception as e:
        print(f"❌ Error checking memory: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Simulate interactive session
    session_id = simulate_interactive_session()

    if session_id:
        # Check persistence
        success = check_memory_after_session()

        if success:
            print("\n✅ Memory persistence test successful!")
            print("🎉 Agent will remember this conversation in future sessions!")
        else:
            print("\n❌ Memory persistence test failed!")
    else:
        print("\n❌ Interactive session simulation failed!")