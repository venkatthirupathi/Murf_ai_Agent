import os
import tempfile
import logging
import assemblyai as aai
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

# Set API key for AssemblyAI
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
if not ASSEMBLYAI_API_KEY:
    logger.error("ASSEMBLYAI_API_KEY not found in environment variables")
    raise Exception("ASSEMBLYAI_API_KEY not found in environment variables")

aai.settings.api_key = ASSEMBLYAI_API_KEY

# Create a transcriber instance
transcriber = aai.Transcriber()

def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe raw audio bytes by writing to a temp file first.
    Returns an empty string on failure.
    """
    if not audio_bytes or len(audio_bytes) == 0:
        logger.error("Empty audio bytes received")
        return ""
    
    temp_path = None
    try:
        # Save bytes to a temporary file; frontend records webm
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            tmp.write(audio_bytes)
            temp_path = tmp.name
        
        logger.info(f"Audio saved to temp file: {temp_path}, size: {len(audio_bytes)} bytes")
        
        # Transcribe using file path (supported by AssemblyAI SDK)
        transcript = transcriber.transcribe(temp_path)
        
        if hasattr(transcript, 'text') and transcript.text:
            logger.info(f"Transcription successful: '{transcript.text[:100]}...'")
            return transcript.text
        else:
            logger.warning("Transcription returned no text")
            return ""
            
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return ""
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.debug(f"Temp file removed: {temp_path}")
            except Exception as cleanup_err:
                logger.warning(f"Failed to remove temp file {temp_path}: {cleanup_err}")
                pass
