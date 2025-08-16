import os
import requests
import logging

logger = logging.getLogger(__name__)

MURF_API_KEY = os.getenv("MURF_API_KEY")
MURF_TTS_ENDPOINT = "https://api.murf.ai/v1/speech/generate-with-key"

def murf_tts(text):
    """Generate TTS using Murf AI API"""
    if not MURF_API_KEY or MURF_API_KEY == "your_murf_api_key_here":
        logger.warning("MURF_API_KEY not configured or using placeholder")
        return None
    
    try:
        headers = {"api-key": MURF_API_KEY, "Content-Type": "application/json"}
        payload = {"voiceId": "en-US-marcus", "text": text, "format": "mp3"}
        
        logger.info(f"Generating TTS for text: {text[:50]}...")
        resp = requests.post(MURF_TTS_ENDPOINT, json=payload, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            audio_url = data.get("audioFile")
            if audio_url:
                logger.info(f"TTS generated successfully: {audio_url}")
                return audio_url
            else:
                logger.error("No audio URL in TTS response")
                return None
        else:
            logger.error(f"TTS API error: {resp.status_code} - {resp.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"TTS request error: {e}")
        return None
    except Exception as e:
        logger.error(f"TTS unexpected error: {e}")
        return None

def fallback_tts(text="I'm having trouble connecting right now."):
    """Generate fallback TTS or return fallback audio file"""
    try:
        # Try to use Murf if available
        if MURF_API_KEY and MURF_API_KEY != "your_murf_api_key_here":
            result = murf_tts(text)
            if result:
                return result
    except Exception as e:
        logger.error(f"Fallback TTS failed: {e}")
    
    # Return fallback audio file path
    return "/static/fallback.mp3"
