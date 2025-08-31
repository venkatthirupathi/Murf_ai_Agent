#!/usr/bin/env python3
"""
Test script for the Agent Persona feature
Tests the persona functionality for Day 24 of 30 Days of AI Voice Agents
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_persona_feature():
    """Test the complete persona feature workflow"""
    print("🎭 Testing Agent Persona Feature - Day 24")
    print("=" * 50)

    # Test session
    session_id = f"test_persona_{int(time.time())}"

    # 1. Test setting different personas
    personas = ["default", "pirate", "robot", "cowboy"]

    for persona in personas:
        print(f"\n1. Testing {persona.upper()} persona...")

        # Set persona
        response = requests.post(f"{BASE_URL}/persona/{session_id}/{persona}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Set persona to {persona}: {data['message']}")
        else:
            print(f"   ❌ Failed to set persona to {persona}")
            return False

        # Get current persona
        response = requests.get(f"{BASE_URL}/persona/{session_id}")
        if response.status_code == 200:
            data = response.json()
            if data['persona'] == persona:
                print(f"   ✅ Confirmed persona is set to {persona}")
            else:
                print(f"   ❌ Persona mismatch: expected {persona}, got {data['persona']}")
                return False
        else:
            print(f"   ❌ Failed to get current persona")
            return False

    # 2. Test persona persistence across sessions
    print("\n2. Testing persona persistence...")
    response = requests.get(f"{BASE_URL}/persona/{session_id}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Persona persists: {data['persona']}")
    else:
        print("   ❌ Persona not persistent")
        return False

    # 3. Test health endpoint
    print("\n3. Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Health check: {data['message']}")
    else:
        print("   ❌ Health check failed")
        return False

    print("\n🎉 All persona tests passed!")
    print("\n📋 Persona Feature Summary:")
    print("   • 🤖 Default AI: Helpful and friendly assistant")
    print("   • 🏴‍☠️ Pirate: Speaks like a pirate captain")
    print("   • 🤖 Robot: Precise, mechanical responses")
    print("   • 🤠 Cowboy: Western slang and frontier spirit")
    print("\n🔗 Access the web interface at: http://localhost:8000")
    print("   Select a persona from the dropdown and click 'Set Persona'")
    print("   Then speak to the AI to see it respond in character!")

    return True

if __name__ == "__main__":
    try:
        test_persona_feature()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        print("Make sure the server is running with: python run.py")
