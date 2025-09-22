#!/usr/bin/env python3
"""
Check what the agent remembers from previous sessions.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent.memory.memory_manager import MemoryManager


def check_memory():
    """Check what's stored in the memory system."""
    print("🧠 Checking Agent Memory")
    print("=" * 50)

    try:
        # Initialize memory manager
        memory_manager = MemoryManager()

        # Check conversations
        print("📜 Stored Conversations:")
        conversations = memory_manager.get_conversation_history()
        if conversations:
            for conv in conversations:
                role = conv.get('role', 'unknown')
                content = conv.get('content', '')[:100]
                timestamp = conv.get('timestamp', '')[:19]
                session = conv.get('session_id', '')[:8]
                print(f"  [{timestamp}] {role}: {content}... (session: {session})")
        else:
            print("  No conversations found")

        print(f"\n📊 Total conversations: {len(conversations)}")

        # Check user profile
        print("\n👤 User Profile:")
        profile = memory_manager.get_user_profile()
        if profile:
            for key, value in profile.items():
                print(f"  {key}: {value}")
        else:
            print("  No profile data")

        # Check facts
        print("\n📝 Stored Facts:")
        facts = memory_manager.get_facts()
        if facts:
            for fact in facts:
                category = fact.get('category', 'unknown')
                content = fact.get('fact', '')[:100]
                confidence = fact.get('confidence', 0)
                source = fact.get('source', 'unknown')
                print(f"  [{category}] {content}... (confidence: {confidence:.1f}, source: {source})")
        else:
            print("  No facts stored")

        # Test semantic search
        print("\n🔍 Testing Semantic Search:")
        if conversations:
            search_results = memory_manager.search_memories("test", method="semantic", limit=3)
            print(f"Found {len(search_results)} results for 'test':")
            for i, result in enumerate(search_results, 1):
                content = result.get('content', '')[:50]
                similarity = result.get('similarity', 0)
                print(f"  {i}. {content}... (similarity: {similarity:.3f})")
        else:
            print("  No conversations to search")

        # Memory statistics
        print("\n📈 Memory Statistics:")
        stats = memory_manager.get_memory_stats()

        # Short-term memory
        short_term = stats.get('short_term', {})
        print(f"  Short-term: {short_term.get('current_messages', 0)}/{short_term.get('max_messages', 0)} messages")

        # Long-term memory
        long_term = stats.get('long_term', {})
        print(f"  Long-term: {long_term.get('conversations_count', 0)} conversations, {long_term.get('facts_count', 0)} facts")
        print(f"  Database size: {long_term.get('database_size_mb', 0)} MB")

        # Smart memory
        smart_memory = stats.get('smart_memory', {})
        if 'total_documents' in smart_memory:
            print(f"  Smart memory: {smart_memory.get('total_documents', 0)} documents")
            print(f"  Vector DB size: {smart_memory.get('storage_size_mb', 0)} MB")
            print(f"  Embedding model: {smart_memory.get('embedding_model', 'unknown')}")
        else:
            print("  Smart memory: not available")

        print("\n" + "=" * 50)
        print("✅ Memory check completed!")

    except Exception as e:
        print(f"❌ Error checking memory: {e}")
        import traceback
        traceback.print_exc()


def test_agent_memory_continuity():
    """Test if agent can remember across sessions."""
    print("\n🤖 Testing Agent Memory Continuity")
    print("=" * 50)

    try:
        from agent import OllamaAgent

        # Initialize agent - this should load existing memory
        print("1. Initializing agent...")
        agent = OllamaAgent(memory_config_path="config/memory_config.yaml")

        # Check if agent has memory tools
        tools = agent.list_tools()
        memory_tools = [tool for tool in tools if any(mem in tool for mem in ['memory', 'profile', 'facts', 'conversation'])]
        print(f"2. Memory tools available: {memory_tools}")

        # Check memory stats through agent
        if agent.memory_manager:
            stats = agent.get_memory_stats()
            print(f"3. Agent memory stats: conversations={stats['long_term']['conversations_count']}, facts={stats['long_term']['facts_count']}")

            # Test if agent can access previous data
            profile = agent.get_user_profile()
            facts = agent.get_facts()

            print(f"4. Agent can access: {len(profile)} profile items, {len(facts)} facts")

            if facts:
                print("5. Sample facts accessible to agent:")
                for fact in facts[:3]:
                    print(f"   - [{fact['category']}] {fact['fact'][:50]}...")

        else:
            print("3. ❌ Agent memory manager not initialized")

        print("\n✅ Agent memory continuity test completed!")

    except Exception as e:
        print(f"❌ Error testing agent: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_memory()
    test_agent_memory_continuity()