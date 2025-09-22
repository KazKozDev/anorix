#!/usr/bin/env python3
"""
Simple test to verify memory tools initialization works without Pydantic errors.
"""

import sys
import os
sys.path.append('/Users/artemk/Projects/anorix')

from agent.tools.memory_search import MemorySearchTool
from agent.tools.profile_tool import ProfileTool
from agent.tools.facts_save import FactsSaveTool
from agent.tools.conversation_history import ConversationHistoryTool

def test_memory_tools():
    """Test that memory tools can be created without errors."""
    print("🧪 Testing memory tools initialization...")

    try:
        # Create mock memory manager (we just need the interface)
        class MockMemoryManager:
            def search_memories(self, query, method, limit):
                return []
            def get_user_profile(self):
                return {}
            def update_user_profile(self, key, value):
                return True
            def save_fact(self, category, fact, source, confidence):
                return True
            def get_facts(self, category=None, min_confidence=0.0):
                return []
            def get_conversation_history(self, days=None, session_id=None, limit=20):
                return []

        mock_mm = MockMemoryManager()

        # Test each tool
        tools = {
            'MemorySearchTool': MemorySearchTool(mock_mm),
            'ProfileTool': ProfileTool(mock_mm),
            'FactsSaveTool': FactsSaveTool(mock_mm),
            'ConversationHistoryTool': ConversationHistoryTool(mock_mm)
        }

        print("✅ All memory tools created successfully!")

        # Test that they can be called (should return error messages since no real memory)
        test_queries = [
            ("MemorySearchTool", lambda t: t._run("test query")),
            ("ProfileTool", lambda t: t._run("get")),
            ("FactsSaveTool", lambda t: t._run("get")),
            ("ConversationHistoryTool", lambda t: t._run())
        ]

        for tool_name, query_func in test_queries:
            try:
                result = query_func(tools[tool_name])
                print(f"✅ {tool_name}._run() works: {result[:50]}...")
            except Exception as e:
                print(f"❌ {tool_name}._run() failed: {e}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_memory_tools()
    if success:
        print("\n🎉 Memory tools initialization test PASSED!")
    else:
        print("\n❌ Memory tools initialization test FAILED!")
        sys.exit(1)
