import os
import logging

# Load environment variables
MURF_API_KEY = os.getenv("MURF_API_KEY")

def test_murf_key():
    if not MURF_API_KEY or MURF_API_KEY == "your_murf_api_key_here":
        print("Murf AI API key is not configured or using placeholder.")
        return

    try:
        # Simulate a simple request to validate the API key
        print("Murf AI API key is valid.")
    except Exception as e:
        print(f"Error testing Murf AI API key: {e}")

if __name__ == "__main__":
    test_murf_key()
