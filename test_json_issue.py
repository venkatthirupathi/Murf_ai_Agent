import json
import requests

def test_json_directly():
    """Test JSON serialization directly"""
    print("Testing JSON serialization directly:")
    
    # Test 1: Direct json.dumps
    test_data = {"test": "value", "another": "field"}
    result = json.dumps(test_data)
    print(f"Direct json.dumps: {result}")
    
    # Test 2: Try to parse it back
    try:
        parsed = json.loads(result)
        print(f"Successfully parsed back: {parsed}")
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw string: {repr(result)}")

def test_endpoint():
    """Test the endpoint"""
    print("\nTesting endpoint:")
    try:
        response = requests.get("http://127.0.0.1:8000/test-json")
        print(f"Status: {response.status_code}")
        print(f"Content: {response.content}")
        print(f"Text: {response.text}")
        
        # Try to parse
        try:
            data = response.json()
            print(f"Parsed JSON: {data}")
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Raw response: {repr(response.text)}")
            
    except Exception as e:
        print(f"Request error: {e}")

if __name__ == "__main__":
    test_json_directly()
    test_endpoint()
