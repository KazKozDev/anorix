#!/usr/bin/env python3
"""
Test script for the three-layer memory system.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent import OllamaAgent


def test_memory_system():
    """Test the memory system functionality."""
    print("🧠 Testing Three-Layer Memory System")
    print("=" * 50)

    try:
        # Initialize agent with memory system
        print("1. Initializing agent with memory system...")
        agent = OllamaAgent(
            model_name="gpt-oss:20b",
            memory_config_path="config/memory_config.yaml",
            verbose=True
        )
        print("✅ Agent initialized successfully")

        # Check memory tools
        print("\n2. Checking available tools...")
        tools = agent.list_tools()
        memory_tools = [tool for tool in tools if any(mem_tool in tool for mem_tool in ['memory', 'profile', 'facts', 'conversation'])]

        print(f"Total tools: {len(tools)}")
        print(f"Memory tools: {memory_tools}")

        # Test memory statistics
        print("\n3. Testing memory statistics...")
        if agent.memory_manager:
            stats = agent.get_memory_stats()
            print(f"Memory stats: {stats}")
        else:
            print("⚠️ Memory manager not available")

        # Test profile operations
        print("\n4. Testing profile operations...")
        success = agent.update_user_profile("name", "Test User")
        print(f"Profile update: {'✅ Success' if success else '❌ Failed'}")

        profile = agent.get_user_profile()
        print(f"Profile data: {profile}")

        # Test fact saving
        print("\n5. Testing fact storage...")
        fact_saved = agent.save_fact(
            category="test",
            fact="This is a test fact about the memory system",
            source="test_script",
            confidence=0.9
        )
        print(f"Fact saved: {'✅ Success' if fact_saved else '❌ Failed'}")

        facts = agent.get_facts(category="test")
        print(f"Retrieved facts: {len(facts)}")

        # Test conversation with memory
        print("\n6. Testing conversation with memory...")

        # First message
        response1 = agent.run("Hello, my name is Alice and I love programming in Python.")
        print(f"Response 1: {response1[:100]}...")

        # Second message that should reference the first
        response2 = agent.run("What programming language did I say I love?")
        print(f"Response 2: {response2[:100]}...")

        # Test memory search
        print("\n7. Testing memory search...")
        if agent.memory_manager:
            search_results = agent.search_memories("programming", method="both", limit=3)
            print(f"Search results: {len(search_results)}")
            for i, result in enumerate(search_results):
                content = result.get('content', '')[:50]
                similarity = result.get('similarity', 0)
                print(f"  {i+1}. {content}... (similarity: {similarity:.2f})")

        print("\n✅ Memory system test completed successfully!")

    except Exception as e:
        print(f"\n❌ Memory system test failed: {e}")
        import traceback
        traceback.print_exc()


def test_memory_tools_directly():
    """Test memory tools directly without agent."""
    print("\n🔧 Testing Memory Tools Directly")
    print("=" * 50)

    try:
        from agent.memory.memory_manager import MemoryManager

        # Initialize memory manager
        print("1. Initializing memory manager...")
        memory_manager = MemoryManager()
        print("✅ Memory manager initialized")

        # Test adding messages
        print("\n2. Testing message storage...")
        memory_manager.add_message("user", "Hello, this is a test message")
        memory_manager.add_message("assistant", "Hello! How can I help you today?")
        print("✅ Messages added")

        # Test profile operations
        print("\n3. Testing profile operations...")
        memory_manager.update_user_profile("test_key", "test_value")
        profile = memory_manager.get_user_profile()
        print(f"Profile: {profile}")

        # Test fact storage
        print("\n4. Testing fact storage...")
        memory_manager.save_fact("testing", "Direct memory manager test", "test", 1.0)
        facts = memory_manager.get_facts()
        print(f"Facts: {len(facts)}")

        # Test search
        print("\n5. Testing memory search...")
        results = memory_manager.search_memories("test", method="both", limit=5)
        print(f"Search results: {len(results)}")

        # Test statistics
        print("\n6. Testing memory statistics...")
        stats = memory_manager.get_memory_stats()
        print(f"Memory stats: {stats}")

        print("\n✅ Direct memory tools test completed!")

    except Exception as e:
        print(f"\n❌ Direct memory tools test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🧠 LangChain Agent Memory System Test")
    print("=" * 60)

    # Test direct memory functionality first
    test_memory_tools_directly()

    # Then test full agent integration
    # test_memory_system()

    print("\n🎉 All tests completed!")