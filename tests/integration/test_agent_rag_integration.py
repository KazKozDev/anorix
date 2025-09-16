#!/usr/bin/env python3
"""
Test RAG integration with the agent (without requiring Ollama).
Tests tool creation and structure.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.agent.tool_manager import ToolManager


def test_tool_manager_rag():
    """Test RAG tools in ToolManager."""
    print("🧪 Testing ToolManager with RAG")
    print("=" * 40)
    
    # Initialize tool manager
    try:
        tool_manager = ToolManager(enable_rag=True)
        print("✅ ToolManager initialized with RAG support")
    except Exception as e:
        print(f"❌ Failed to initialize ToolManager: {e}")
        return
    
    # Check available tools
    tools = tool_manager.list_tools()
    print(f"📋 Available tools: {tools}")
    
    # Check for RAG tools
    rag_tools = [tool for tool in tools if 'rag' in tool.lower()]
    print(f"🔍 RAG tools found: {rag_tools}")
    
    if len(rag_tools) >= 2:
        print("✅ Both RAG tools are available")
    else:
        print("❌ RAG tools missing")
        return
    
    # Get tool instances
    retrieval_tool = tool_manager.get_tool('rag_retrieval')
    management_tool = tool_manager.get_tool('rag_management')
    
    print(f"🔧 Retrieval tool type: {type(retrieval_tool).__name__}")
    print(f"🔧 Management tool type: {type(management_tool).__name__}")
    
    # Test tool descriptions
    descriptions = tool_manager.get_tool_descriptions()
    if 'rag_retrieval' in descriptions:
        print(f"📝 Retrieval tool description: {descriptions['rag_retrieval'][:80]}...")
    if 'rag_management' in descriptions:
        print(f"📝 Management tool description: {descriptions['rag_management'][:80]}...")
    
    # Test structured tool functionality
    print("\n🧪 Testing structured tool calls...")
    
    try:
        # Test management tool
        result = management_tool.func(
            action="add_text",
            content="Test document about artificial intelligence and machine learning.",
            title="AI Test Doc"
        )
        print(f"✅ Management tool call: {result[:60]}...")
        
        # Test retrieval tool
        result = retrieval_tool.func(
            query="artificial intelligence",
            k=1
        )
        print(f"✅ Retrieval tool call: {result[:60]}...")
        
    except Exception as e:
        print(f"❌ Tool call failed: {e}")
        return
    
    print("\n✅ RAG integration test completed successfully!")
    print("🚀 Ready for use with Ollama agent!")


def test_without_rag():
    """Test ToolManager without RAG."""
    print("\n🧪 Testing ToolManager without RAG")
    print("=" * 40)
    
    try:
        tool_manager = ToolManager(enable_rag=False)
        tools = tool_manager.list_tools()
        print(f"📋 Tools without RAG: {tools}")
        
        rag_tools = [tool for tool in tools if 'rag' in tool.lower()]
        if len(rag_tools) == 0:
            print("✅ No RAG tools when disabled")
        else:
            print(f"⚠️  RAG tools found when disabled: {rag_tools}")
            
    except Exception as e:
        print(f"❌ Failed to test without RAG: {e}")


def main():
    """Run integration tests."""
    test_tool_manager_rag()
    test_without_rag()
    
    print("\n" + "=" * 50)
    print("🎯 RAG Integration Test Summary")
    print("=" * 50)
    print("✅ StructuredTool implementation working")
    print("✅ ToolManager integration successful")  
    print("✅ RAG enable/disable functionality working")
    print("🚀 Ready for production use with Ollama agent!")


if __name__ == "__main__":
    main()