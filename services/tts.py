# import requests
# import os

# MURF_API_KEY = os.getenv("MURF_API_KEY")
# MURF_TTS_ENDPOINT = "https://api.murf.ai/v1/speech/generate-with-key"

# def murf_tts(text: str) -> str:
#     headers = {"api-key": MURF_API_KEY, "Content-Type": "application/json"}
#     payload = {"voiceId": "en-US-marcus", "text": text, "format": "mp3"}
#     resp = requests.post(MURF_TTS_ENDPOINT, json=payload, headers=headers)
#     resp.raise_for_status()
#     return resp.json().get("audioFile")


import os
import requests

MURF_API_KEY = os.getenv("MURF_API_KEY")
MURF_TTS_ENDPOINT = "https://api.murf.ai/v1/speech/generate-with-key"

def murf_tts(text):
    if not MURF_API_KEY:
        raise Exception("MURF_API_KEY not found in environment variables")
    
    headers = {"api-key": MURF_API_KEY, "Content-Type": "application/json"}
    payload = {"voiceId": "en-US-marcus", "text": text, "format": "mp3"}
    resp = requests.post(MURF_TTS_ENDPOINT, json=payload, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    return data.get("audioFile")

def fallback_tts(text="I'm having trouble connecting right now."):
    try:
        return murf_tts(text)
    except Exception:
        return "/static/fallback.mp3"
