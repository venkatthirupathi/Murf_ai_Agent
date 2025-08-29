import requests
import json

def test_joke_endpoint():
    """Test the joke endpoint"""
    base_url = "http://localhost:8000"  # Assuming FastAPI runs on default port
    
    try:
        # Test the joke endpoint
        response = requests.get(f"{base_url}/joke")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Joke endpoint test PASSED")
            print(f"Audio URL: {result.get('audio_url')}")
            print(f"Joke text: {result.get('text', 'Not available')}")
            if result.get('error'):
                print(f"Warning: Error message present: {result['error']}")
            return True
        else:
            print(f"❌ Joke endpoint test FAILED - Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the FastAPI server is running.")
        print("Run: uvicorn app:app --reload")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_joke_endpoint()
