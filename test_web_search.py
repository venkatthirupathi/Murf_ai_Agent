#!/usr/bin/env python3
"""
Test script for web search functionality
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.web_search import perform_web_search, get_news, get_weather

def test_web_search():
    """Test web search functionality"""
    print("🧪 Testing Web Search Functionality")
    print("=" * 50)
    
    # Check if API key is configured
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key or tavily_api_key == "your_tavily_api_key_here":
        print("❌ TAVILY_API_KEY not configured or using placeholder")
        print("   Please add your Tavily API key to the .env file")
        return False
    
    print("✅ TAVILY_API_KEY is configured")
    
    # Test 1: Basic web search
    print("\n1. Testing basic web search...")
    results = perform_web_search("latest AI developments", 2)
    
    if results is None:
        print("❌ Web search failed - service unavailable")
        return False
    
    print(f"✅ Found {len(results)} results")
    for i, result in enumerate(results, 1):
        print(f"   {i}. {result.get('title', 'No title')}")
        print(f"      URL: {result.get('url', 'No URL')}")
        print(f"      Content: {result.get('content', 'No content')[:100]}...")
        print()
    
    # Test 2: News search
    print("\n2. Testing news search...")
    news_results = get_news("technology", 3)
    
    if news_results is None:
        print("❌ News search failed - service unavailable")
        return False
    
    print(f"✅ Found {len(news_results)} news items")
    for i, result in enumerate(news_results, 1):
        print(f"   {i}. {result.get('title', 'No title')}")
        print(f"      {result.get('content', 'No content')[:80]}...")
        print()
    
    # Test 3: Weather search
    print("\n3. Testing weather search...")
    weather_results = get_weather("San Francisco")
    
    if weather_results is None:
        print("❌ Weather search failed - service unavailable")
        return False
    
    print(f"✅ Found {len(weather_results)} weather results")
    for i, result in enumerate(weather_results, 1):
        print(f"   {i}. {result.get('title', 'No title')}")
        print(f"      {result.get('content', 'No content')[:100]}...")
        print()
    
    print("🎉 All web search tests completed successfully!")
    return True

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    success = test_web_search()
    sys.exit(0 if success else 1)
