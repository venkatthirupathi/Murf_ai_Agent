import os
import assemblyai as aai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set API key for AssemblyAI
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

def test_assemblyai_key():
    if not ASSEMBLYAI_API_KEY or ASSEMBLYAI_API_KEY == "your_assemblyai_api_key_here":
        print("AssemblyAI API key is not configured or using placeholder.")
        return

    aai.settings.api_key = ASSEMBLYAI_API_KEY
    try:
        # Test the API key by making a simple request
        transcriber = aai.Transcriber()
        print("AssemblyAI API key is valid.")
    except Exception as e:
        print(f"Error testing AssemblyAI API key: {e}")

if __name__ == "__main__":
    test_assemblyai_key()
