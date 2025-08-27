import os
import asyncio
import websockets
import json
from dotenv import load_dotenv

load_dotenv()

MURF_API_KEY = os.getenv("MURF_API_KEY")
MURF_WS_URL = "wss://api.murf.ai/v1/speech/generate"  # Correct endpoint

async def send_text_and_receive_audio(text, context_id="static-context-id"):
    if not MURF_API_KEY:
        print("Error: MURF_API_KEY not found in environment variables.")
        return
    try:
        async with websockets.connect(MURF_WS_URL) as ws:
            payload = {
                "api_key": MURF_API_KEY,
                "context_id": context_id,
                "text": text
            }
            await ws.send(json.dumps(payload))
            async for message in ws:
                data = json.loads(message)
                if "audio_base64" in data:
                    print("Base64 Audio:", data["audio_base64"])
                    break
                elif "error" in data:
                    print("Error:", data["error"])
                    break
    except Exception as e:
        print(f"WebSocket connection failed: {e}")

if __name__ == "__main__":
    text = "Hello, this is a test of Murf Websockets."
    asyncio.run(send_text_and_receive_audio(text))