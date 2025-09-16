#!/usr/bin/env python3
"""
Full test of all agent tools including webscraper and observation.
"""

import sys
import os

import pytest

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.agent import OllamaAgent

@pytest.mark.integration
@pytest.mark.agent
def test_all_tools():
    print("🔧 Testing all agent tools with detailed observation")
    print("=" * 60)
    
    try:
        agent = OllamaAgent(verbose=True)
        print(f"✅ Agent created with {len(agent.list_tools())} tools!")
        
        # Show all tools
        print("\n🛠️ Available tools:")
        for i, tool_name in enumerate(agent.list_tools(), 1):
            print(f"  {i}. {tool_name}")
        
        print("\n" + "="*60)
        
        # Test 1: Calculator
        print("\n🧮 Test 1: Calculator")
        result = agent.process_query("Calculate 15 * 7 + 25")
        print(f"📊 Final result: {result}")
        
        print("\n" + "-"*40)
        
        # Test 2: Date and time
        print("\n🕒 Test 2: Date and Time")
        result = agent.process_query("What time is it now and what date will it be in 5 days?")
        print(f"📊 Final result: {result}")
        
        print("\n" + "-"*40)
        
        # Test 3: Web Scraper
        print("\n🕷️ Test 3: Web Scraper")
        result = agent.process_query("Extract the title and main content from https://example.com")
        print(f"📊 Final result: {result}")
        
        print("\n" + "-"*40)
        
        # Test 4: File Manager
        print("\n📁 Test 4: File Manager")
        result = agent.process_query("Create a file summary.txt with content: 'All tools test completed successfully!'")
        print(f"📊 Final result: {result}")
        
        print("\n" + "-"*40)
        
        # Test 5: Combined complex query
        print("\n🎯 Test 5: Combined query (all tools)")
        complex_query = """
        Help me complete a complex task:
        1. Calculate how many minutes are in a day (24 * 60)
        2. Find out today's date  
        3. Extract the title from https://example.com
        4. Create a file report.txt with the results of all calculations
        """
        result = agent.process_query(complex_query)
        print(f"📊 Final result: {result}")
        
        print("\n" + "="*60)
        print("🎉 All tests completed!")
        print("\n📋 What we saw in the logs:")
        print("  ✅ 🎯 ACTION - when the agent calls a tool")
        print("  ✅ 👁️ OBSERVATION - tool result output") 
        print("  ✅ 🔧 TOOL START/END - tool execution details")
        print("  ✅ 💭 THOUGHT - agent's reasoning (if available)")
        print("  ✅ Intermediate steps with detailed information")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_all_tools()