import requests
import json

def test_streaming():
    print("Testing streaming functionality...")
    
    # Test the streaming endpoint
    try:
        with open('test_audio.wav', 'rb') as audio_file:
            files = {'file': ('test_audio.wav', audio_file, 'audio/wav')}
            response = requests.post('http://localhost:8000/agent/chat/test_session_123/stream', files=files)
            
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                print("Streaming test successful!")
                print("Response:", response.text)
            else:
                print(f"Error: {response.text}")
                
    except Exception as e:
        print(f"Error during streaming test: {e}")

if __name__ == "__main__":
    test_streaming()
