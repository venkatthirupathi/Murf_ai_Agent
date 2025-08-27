#!/usr/bin/env python3
"""
Manual test script for the web search API endpoint
This shows how to test the endpoint using requests
"""

import requests
import json
import sys

def test_web_search_endpoint():
    """Test the web search endpoint manually"""
    print("🌐 Testing Web Search API Endpoint Manually")
    print("=" * 50)
    
    # Base URL for the API
    base_url = "http://localhost:8000"
    
    print(f"Testing endpoint: {base_url}/web-search")
    print()
    
    # Test data
    test_queries = [
        {"query": "latest AI developments", "max_results": 2},
        {"query": "Python programming news", "max_results": 1},
        {"query": "weather in San Francisco"}
    ]
    
    print("📋 Test queries prepared:")
    for i, query in enumerate(test_queries, 1):
        print(f"   {i}. {json.dumps(query)}")
    
    print()
    print("💡 To test manually, run the server and use one of these commands:")
    print()
    
    for query in test_queries:
        curl_command = f'curl -X POST "{base_url}/web-search" \\\n'
        curl_command += '  -H "Content-Type: application/json" \\\n'
        curl_command += f'  -d \'{json.dumps(query)}\''
        print(curl_command)
        print()
    
    print("📝 Or use Python requests:")
    print()
    for query in test_queries:
        python_code = f'import requests\n'
        python_code += f'import json\n\n'
        python_code += f'response = requests.post(\n'
        python_code += f'    "{base_url}/web-search",\n'
        python_code += f'    headers={{"Content-Type": "application/json"}},\n'
        python_code += f'    data=json.dumps({query})\n'
        python_code += f')\n\n'
        python_code += f'print(response.json())'
        print(python_code)
        print("-" * 40)
        print()
    
    return True

if __name__ == "__main__":
    print("🔧 Web Search API Manual Test Guide")
    print("This script shows how to manually test the web search endpoint")
    print()
    
    success = test_web_search_endpoint()
    
    if success:
        print("✅ Manual test guide generated successfully!")
        print("\n🚀 To run the server:")
        print("   python run.py")
        print("\n📚 Then use the provided commands to test the API")
    else:
        print("❌ Failed to generate test guide")
    
    sys.exit(0 if success else 1)
