#!/usr/bin/env python3
"""
Test querying the bitcoin price.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.agent import OllamaAgent

def test_bitcoin_price():
    print("🪙 Testing bitcoin price query...")
    
    try:
        agent = OllamaAgent(verbose=True)
        print("✅ Agent created!")
        
        print("\n🔍 Query: bitcoin price")
        result = agent.process_query("bitcoin price")
        print(f"\n📊 Result:\n{result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bitcoin_price()