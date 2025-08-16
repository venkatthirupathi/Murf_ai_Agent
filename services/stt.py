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

def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe raw audio bytes by writing to a temp file first.
    Returns an empty string on failure.
    """
    if not audio_bytes or len(audio_bytes) == 0:
        logger.error("Empty audio bytes received")
        return ""
    
    # Check if API key is configured
    if not ASSEMBLYAI_API_KEY or ASSEMBLYAI_API_KEY == "your_assemblyai_api_key_here":
        logger.error("ASSEMBLYAI_API_KEY not configured or using placeholder")
        return "API key not configured. Please add your AssemblyAI API key to the .env file."
    
    try:
        # Configure AssemblyAI
        aai.settings.api_key = ASSEMBLYAI_API_KEY
        transcriber = aai.Transcriber()
        
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
            return "Speech could not be understood. Please try speaking more clearly."
            
    except aai.APIError as e:
        if "401" in str(e):
            logger.error("AssemblyAI API key invalid or expired")
            return "API key error. Please check your AssemblyAI API key."
        elif "429" in str(e):
            logger.error("AssemblyAI rate limit exceeded")
            return "Rate limit exceeded. Please try again later."
        else:
            logger.error(f"AssemblyAI API error: {e}")
            return f"Transcription error: {str(e)}"
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return f"Transcription failed: {str(e)}"
    finally:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.debug(f"Temp file removed: {temp_path}")
            except Exception as cleanup_err:
                logger.warning(f"Failed to remove temp file {temp_path}: {cleanup_err}")
                pass
