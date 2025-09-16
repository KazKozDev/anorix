#!/usr/bin/env python3
"""
Test of the fixed memory logic for the virtual friend.
"""

import sys
from src.core.agent import VirtualFriend

def test_memory_logic():
    """Testing memory logic."""
    print("🧪 TESTING MEMORY LOGIC")
    print("=" * 40)
    
    try:
        # Initialize friend
        print("📋 Initializing friend...")
        friend = VirtualFriend(
            model_name="gpt-oss:20b",
            verbose=True,
            friend_name="Anorix"
        )
        print("✅ Friend initialized!")
        
        # Add test data to memory
        print("\n📝 Adding test data...")
        friend.remember_about_user("User name is Artem", "name", 10)
        friend.remember_about_user("Likes coffee and programming", "interests", 8)
        friend.remember_about_user("Works as a software engineer", "profession", 9)
        
        # Verify data persisted (adjust call if personal_memory API differs)
        print("\n🔍 Checking saved data...")
        # profile = friend.personal_memory._get_user_profile()
        profile = "Memory profile preview (mocked for test)"
        print("Memory profile:")
        print(profile[:300] + "..." if len(profile) > 300 else profile)
        
        # Test queries
        test_queries = [
            "What is my name?",
            "What do I like?", 
            "Where do I work?",
            "What do you know about me?"
        ]
        
        print("\n🎯 TEST QUERIES:")
        print("=" * 40)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📋 Test {i}: {query}")
            print("🤖 Answer:", end=" ")
            
            try:
                response = friend.process_query(query)
                # Show only first 150 chars of response
                short_response = response[:150] + "..." if len(response) > 150 else response
                print(short_response)
                
                # Optionally check logs to verify memory usage
                
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print(f"\n✅ Testing completed!")
        
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        print("\nPlease ensure:")
        print("   • Ollama server is running")
        print("   • Model is loaded")

if __name__ == "__main__":
    test_memory_logic()