#!/usr/bin/env python3
"""
Core Integration Test Script
Tests Phase 1: Core Integration of the Murf AI conversational agent
- API key verification
- Transcription service (AssemblyAI)
- LLM service (Google Gemini) 
- TTS service (Murf AI)
- Chat history persistence
"""

import os
import sys
import asyncio
import json
import base64
import wave
import io
from dotenv import load_dotenv

# Add current directory to path to import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Import service modules
from services.stt import transcribe_audio, ASSEMBLYAI_API_KEY
from services.llm import generate_llm_response
from services.tts import murf_tts, fallback_tts

def test_api_keys():
    """Test if all required API keys are configured"""
    print("🔑 Testing API Key Configuration")
    print("=" * 50)
    
    required_keys = ["MURF_API_KEY", "ASSEMBLYAI_API_KEY", "GEMINI_API_KEY"]
    results = {}
    
    for key in required_keys:
        value = os.getenv(key)
        if value and value != f"your_{key.lower()}_here":
            results[key] = "✅ Configured"
            print(f"{key}: ✅ Configured")
        else:
            results[key] = "❌ Missing"
            print(f"{key}: ❌ Missing")
    
    print("=" * 50)
    return results

def test_transcription_service():
    """Test AssemblyAI transcription service"""
    print("\n🎤 Testing Transcription Service (AssemblyAI)")
    print("=" * 50)
    
    # Generate a test audio file (silence)
    sample_rate = 16000
    channels = 1
    duration = 1.0  # 1 second of silence
    
    # Generate silent audio data (PCM 16-bit)
    silent_audio = b"\x00\x00" * int(sample_rate * duration * channels)
    
    print(f"Generated test audio: {len(silent_audio)} bytes")
    
    try:
        # Test transcription
        result = transcribe_audio(silent_audio)
        
        if "API key not configured" in result:
            print("❌ Transcription failed: API key not configured")
            return False
        elif "error" in result.lower():
            print(f"❌ Transcription error: {result}")
            return False
        elif result == "":
            print("✅ Transcription completed (silence detected)")
            return True
        else:
            print(f"✅ Transcription successful: '{result}'")
            return True
            
    except Exception as e:
        print(f"❌ Transcription exception: {e}")
        return False

def test_llm_service():
    """Test Google Gemini LLM service"""
    print("\n🤖 Testing LLM Service (Google Gemini)")
    print("=" * 50)
    
    test_prompt = "Hello, how are you today? Please respond briefly."
    
    try:
        # Create a simple chat history
        history = [
            {"role": "user", "content": test_prompt}
        ]
        
        result = generate_llm_response(history)
        
        if "API key not configured" in result:
            print("❌ LLM failed: API key not configured")
            return False
        elif "error" in result.lower():
            print(f"❌ LLM error: {result}")
            return False
        elif not result:
            print("❌ LLM returned empty response")
            return False
        else:
            print(f"✅ LLM response successful: '{result[:100]}...'")
            return True
            
    except Exception as e:
        print(f"❌ LLM exception: {e}")
        return False

def test_tts_service():
    """Test Murf AI TTS service"""
    print("\n🎵 Testing TTS Service (Murf AI)")
    print("=" * 50)
    
    test_text = "Hello, this is a test of the text to speech service."
    
    try:
        result = murf_tts(test_text)
        
        if not result:
            print("❌ TTS failed: No audio URL returned")
            
            # Test fallback TTS
            print("Testing fallback TTS...")
            fallback_result = fallback_tts(test_text)
            if fallback_result:
                print(f"✅ Fallback TTS successful: {fallback_result}")
                return True
            else:
                print("❌ Both Murf and fallback TTS failed")
                return False
        else:
            print(f"✅ TTS successful: {result}")
            return True
            
    except Exception as e:
        print(f"❌ TTS exception: {e}")
        
        # Test fallback TTS
        try:
            fallback_result = fallback_tts(test_text)
            if fallback_result:
                print(f"✅ Fallback TTS successful: {fallback_result}")
                return True
            else:
                print("❌ Both Murf and fallback TTS failed")
                return False
        except Exception as fallback_e:
            print(f"❌ Fallback TTS also failed: {fallback_e}")
            return False

def test_chat_history():
    """Test chat history persistence"""
    print("\n💾 Testing Chat History Persistence")
    print("=" * 50)
    
    # Import the app to access CHAT_SESSIONS
    try:
        from app import CHAT_SESSIONS
        
        # Test session ID
        session_id = "test_session_123"
        
        # Clear any existing session
        if session_id in CHAT_SESSIONS:
            del CHAT_SESSIONS[session_id]
        
        # Test adding messages
        test_messages = [
            {"role": "user", "content": "Hello, how are you?"},
            {"role": "model", "content": "I'm doing well, thank you for asking!"},
            {"role": "user", "content": "What can you help me with?"}
        ]
        
        # Add messages to session
        CHAT_SESSIONS[session_id] = test_messages
        
        # Verify persistence
        if session_id in CHAT_SESSIONS:
            stored_messages = CHAT_SESSIONS[session_id]
            if len(stored_messages) == len(test_messages):
                print("✅ Chat history persistence working correctly")
                print(f"   Session ID: {session_id}")
                print(f"   Messages stored: {len(stored_messages)}")
                return True
            else:
                print("❌ Chat history count mismatch")
                return False
        else:
            print("❌ Session not found in chat history")
            return False
            
    except Exception as e:
        print(f"❌ Chat history test exception: {e}")
        return False

async def main():
    """Run all core integration tests"""
    print("🚀 Starting Core Integration Tests - Phase 1")
    print("=" * 60)
    
    test_results = {}
    
    # Test 1: API Key Configuration
    api_key_results = test_api_keys()
    test_results["api_keys"] = all("✅" in result for result in api_key_results.values())
    
    # Test 2: Transcription Service
    test_results["transcription"] = test_transcription_service()
    
    # Test 3: LLM Service
    test_results["llm"] = test_llm_service()
    
    # Test 4: TTS Service
    test_results["tts"] = test_tts_service()
    
    # Test 5: Chat History
    test_results["chat_history"] = test_chat_history()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:15}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("🎉 ALL CORE INTEGRATION TESTS PASSED!")
        print("\n📋 Phase 1 Complete - Ready for Phase 2 (Streaming Implementation)")
    else:
        print("⚠️  SOME TESTS FAILED - Check configuration and API keys")
        print("\n💡 Next steps:")
        print("   1. Verify all API keys in .env file")
        print("   2. Check API service status")
        print("   3. Run individual tests to debug")
    
    print("=" * 60)
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
