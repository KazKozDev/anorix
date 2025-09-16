#!/usr/bin/env python3
"""
Test script for the advanced voice system
"""

import asyncio
import logging
import sys
import os

import pytest

# Add project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)

@pytest.mark.integration
@pytest.mark.voice
@pytest.mark.asyncio
async def test_voice_processor():
    """Test voice processor independently."""
    print("🧪 Testing Voice Processor...")
    
    try:
        from src.core.voice_engine import VoiceProcessor
        
        # Test initialization
        processor = VoiceProcessor(whisper_model="tiny", verbose=True)
        
        # Test model loading
        success = await processor.initialize_models()
        print(f"✅ Models loaded: {success}")
        
        if success:
            # Test TTS
            audio_bytes = await processor.generate_speech("Hello! This is a test of the Ajax voice system.")
            if audio_bytes:
                # Save test audio
                processor.save_audio_file(audio_bytes, "test_voice_output.wav")
                print("✅ Test audio saved to test_voice_output.wav")
            
        await processor.close()
        return success
        
    except Exception as e:
        print(f"❌ Voice processor test failed: {e}")
        return False

async def test_webrtc_server():
    """Test WebRTC server."""
    print("🧪 Testing WebRTC Server...")
    
    try:
        from voice_engine import WebRTCVoiceServer
        
        # Create server
        server = WebRTCVoiceServer(verbose=True)
        
        # Create test session
        session_id = await server.create_session()
        print(f"✅ Created session: {session_id}")
        
        # Get session info
        info = await server.get_session_info(session_id)
        print(f"✅ Session info: {info}")
        
        # Close session
        await server.close_session(session_id)
        print("✅ Session closed")
        
        return True
        
    except Exception as e:
        print(f"❌ WebRTC server test failed: {e}")
        return False

async def test_friend_integration():
    """Test integration with virtual friend."""
    print("🧪 Testing Friend Integration...")
    
    try:
        from src.core.agent import VirtualFriend
        from voice_engine import WebRTCVoiceServer
        
        # Initialize friend
        friend = VirtualFriend(
            model_name="gpt-oss:20b",
            temperature=0.2,
            friend_name="Ajax"
        )
        print("✅ Virtual friend initialized")
        
        # Create voice server with friend
        server = WebRTCVoiceServer(friend_instance=friend, verbose=True)
        
        # Test session
        session_id = await server.create_session()
        print(f"✅ Voice session with friend: {session_id}")
        
        # Test TTS with friend context
        await server.send_text_to_session(session_id, "Hello! I am Ajax, your virtual friend with a new voice system!")
        print("✅ TTS with friend context successful")
        
        # Cleanup
        await server.close_session(session_id)
        
        return True
        
    except Exception as e:
        print(f"❌ Friend integration test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting Advanced Voice System Tests\n")
    
    tests = [
        ("Voice Processor", test_voice_processor),
        ("WebRTC Server", test_webrtc_server),
        ("Friend Integration", test_friend_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 {test_name}")
        print('='*50)
        
        try:
            result = await test_func()
            results[test_name] = result
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            results[test_name] = False
            print(f"\n❌ ERROR in {test_name}: {e}")
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 TEST SUMMARY")
    print('='*50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Voice system is ready.")
    else:
        print("⚠️ Some tests failed. Check dependencies and configuration.")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)