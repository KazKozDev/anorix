#!/usr/bin/env python3
"""
Simple test to verify the agent works without _extract_user_info errors.
"""

import sys
import os
sys.path.append('/Users/artemk/Projects/anorix')

def test_agent_basic():
    """Test basic agent functionality."""
    print("🧪 Testing basic agent functionality...")

    try:
        from agent.core import OllamaAgent

        # Create agent with minimal config
        agent = OllamaAgent(
            model_name="gpt-oss:20b",
            verbose=False,
            memory_config_path="config/memory_config.yaml"
        )

        print("✅ Agent created successfully")
        print(f"✅ Memory manager: {'Available' if agent.memory_manager else 'Not available'}")
        print(f"✅ Tools loaded: {len(agent.list_tools())}")

        # Test basic query processing
        test_query = "Hello, how are you?"
        result = agent.process_query(test_query)

        print(f"✅ Query processed successfully: {result[:50]}...")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_agent_basic()
    if success:
        print("\n🎉 Basic agent test PASSED!")
    else:
        print("\n❌ Basic agent test FAILED!")
        sys.exit(1)
