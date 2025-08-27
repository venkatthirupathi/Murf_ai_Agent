import requests
import json

def test_persona_endpoints():
    base_url = "http://127.0.0.1:8000"
    session_id = "test_session_123"
    
    # Test setting persona
    print("Testing persona setting...")
    try:
        response = requests.post(f"{base_url}/persona/{session_id}/pirate")
        print(f"Status Code: {response.status_code}")
        print(f"Response Content: {response.content}")
        print(f"Response Text: {response.text}")
        
        # Parse the custom format
        data = {}
        if "|" in response.text:
            for part in response.text.split("|"):
                if ":" in part:
                    key, value = part.split(":", 1)
                    data[key] = value
            print(f"Parsed custom format: {data}")
            
    except Exception as e:
        print(f"Request Error: {e}")
    
    # Test getting persona
    print("\nTesting persona retrieval...")
    try:
        response = requests.get(f"{base_url}/persona/{session_id}")
        print(f"Status Code: {response.status_code}")
        print(f"Response Content: {response.content}")
        print(f"Response Text: {response.text}")
        
        # Parse the custom format
        data = {}
        if "|" in response.text:
            for part in response.text.split("|"):
                if ":" in part:
                    key, value = part.split(":", 1)
                    data[key] = value
            print(f"Parsed custom format: {data}")
            
    except Exception as e:
        print(f"Request Error: {e}")

if __name__ == "__main__":
    test_persona_endpoints()
