#!/usr/bin/env python3
"""
Test script for the joke generator special skill
"""

import requests
import json
import sys

def test_joke_skill():
    """Test the joke generator endpoint"""
    print("🎭 Testing Joke Generator Special Skill")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    try:
        # Test the joke endpoint
        print("\n1. Testing /agent/skill/joke endpoint...")
        response = requests.post(
            f"{base_url}/agent/skill/joke",
            headers={"Content-Type": "application/json"},
            json={}
        )
        
        if response.status_code == 200:
            joke_data = response.json()
            print(f"✅ Success! Joke received:")
            print(f"   Setup: {joke_data.get('setup', 'No setup')}")
            print(f"   Punchline: {joke_data.get('punchline', 'No punchline')}")
            return True
        else:
            print(f"❌ Failed with status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the server is running.")
        print("   Start the server with: uvicorn app:app --reload")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_joke_skill()
    sys.exit(0 if success else 1)
