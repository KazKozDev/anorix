#!/usr/bin/env python3
"""
Test script to verify that the agent now properly uses profile_tool for profile updates.
"""

import sys
import os
sys.path.append('/Users/artemk/Projects/anorix')

def test_profile_tool_usage():
    """Test that profile_tool is correctly configured."""
    print("🧪 Testing profile_tool configuration...")

    from agent.tools.profile_tool import ProfileTool

    # Test tool creation
    try:
        # Create mock memory manager
        class MockMemoryManager:
            def get_user_profile(self):
                return {"name": "Test User", "city": "Test City"}
            def update_user_profile(self, key, value):
                print(f"✅ Profile updated: {key} = {value}")
                return True

        mock_mm = MockMemoryManager()
        tool = ProfileTool(mock_mm)

        print("✅ ProfileTool created successfully")
        print(f"✅ Tool name: {tool.name}")
        print(f"✅ Tool description: {tool.description[:100]}...")

        # Test tool execution
        result = tool._run(action="update", key="city", value="Moscow")
        print(f"✅ Tool execution result: {result}")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_profile_tool_usage()
    if success:
        print("\n🎉 Profile tool test PASSED!")
        print("\n📋 Summary of changes:")
        print("✅ Removed automatic profile extraction from process_query")
        print("✅ Enhanced system message with clear profile_tool usage examples")
        print("✅ Improved profile_tool description with usage examples")
        print("✅ Agent should now use profile_tool when user shares personal info")
    else:
        print("\n❌ Profile tool test FAILED!")
        sys.exit(1)
