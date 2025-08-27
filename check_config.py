#!/usr/bin/env python3
"""
Configuration Check Script
Checks if all required API keys are properly configured in the .env file
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_api_keys():
    """Check if all required API keys are configured"""
    print("🔍 Checking API Key Configuration")
    print("=" * 50)
    
    required_keys = ["MURF_API_KEY", "ASSEMBLYAI_API_KEY", "GEMINI_API_KEY"]
    all_configured = True
    
    for key in required_keys:
        value = os.getenv(key)
        if value and value != f"your_{key.lower().replace('_api_key', '')}_api_key_here":
            status = "✅ Configured"
        else:
            status = "❌ Missing"
            all_configured = False
        
        print(f"{key:20}: {status}")
        if value:
            print(f"   Value: {value[:20]}...")  # Show first 20 chars for verification
        else:
            print(f"   Value: Not set")
    
    print("=" * 50)
    
    if all_configured:
        print("🎉 All API keys are properly configured!")
        print("\nNext steps:")
        print("1. Run integration tests: python test_core_integration.py")
        print("2. Start the application: uvicorn app:app --reload")
        print("3. Test the web interface at http://localhost:8000")
    else:
        print("⚠️  Some API keys are missing or using placeholder values")
        print("\nPlease update the .env file with your actual API keys:")
        print("- Murf AI: https://murf.ai")
        print("- AssemblyAI: https://assemblyai.com")
        print("- Google Gemini: https://makersuite.google.com/app/apikey")
    
    print("=" * 50)
    return all_configured

if __name__ == "__main__":
    check_api_keys()
