import os
import logging
import json
from typing import AsyncGenerator
from queue import Queue, Empty
import assemblyai as aai
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Path
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from schemas.audio import SpeechRequest, SpeechResponse
from schemas.chat import ChatResponse

from services.tts import murf_tts, fallback_tts
from services.stt import transcribe_audio
from services.llm_day24 import generate_llm_response
from custom_json import custom_json_dumps

load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHAT_SESSIONS = {}

UPLOAD_DIRECTORY = "uploads"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

# Validate required environment variables
required_env_vars = ["MURF_API_KEY", "ASSEMBLYAI_API_KEY", "GEMINI_API_KEY"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.warning(f"Missing environment variables: {missing_vars}")

app = FastAPI(title="AI Voice Agent - Day 24: Agent Persona", description="Voice-first conversational AI agent with persona functionality")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Fallback WAV generator to avoid missing static asset errors
import io
import wave

def _generate_silence_wav_bytes(duration_secs: float = 0.5, sample_rate: int = 16000) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * int(duration_secs * sample_rate))
    return buffer.getvalue()

@app.get("/fallback.wav")
async def fallback_wav():
    data = _generate_silence_wav_bytes()
    return Response(content=data, media_type="audio/wav")

@app.get("/favicon.ico")
async def favicon():
    # 1x1 transparent PNG data
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\x0bIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\x0d\n\x2d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return Response(content=png_bytes, media_type="image/png")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate-audio", response_model=SpeechResponse)
def generate_audio(request: SpeechRequest):
    input_text = request.text.strip()
    if not input_text:
        raise HTTPException(status_code=400, detail="Input text cannot be empty")

    try:
        audio_url = murf_tts(input_text)
        if not audio_url:
            raise Exception("No audio URL returned from Murf TTS")
        return SpeechResponse(audio_url=audio_url)
    except Exception as err:
        logger.error(f"Murf TTS error: {err}")
        try:
            fallback_url = fallback_tts("I'm having trouble generating audio right now.")
            return SpeechResponse(audio_url=fallback_url, error=str(err))
        except Exception as fallback_err:
            logger.error(f"Fallback TTS also failed: {fallback_err}")
            return SpeechResponse(audio_url="/fallback.wav", error=str(err))

@app.post("/agent/chat/{session_id}", response_model=ChatResponse)
async def agent_chat(session_id: str = Path(...), file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")

    if not file.content_type or not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")

    try:
        audio_data = await file.read()
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")

        logger.info(f"Received audio file: {file.filename}, size: {len(audio_data)} bytes, type: {file.content_type}")

        user_text = transcribe_audio(audio_data)
        if not user_text:
            logger.error("Transcription returned empty result")
            raise Exception("Speech could not be understood. Please try speaking more clearly.")

        # Check if transcription returned an error message
        if "API key not configured" in user_text or "error" in user_text.lower():
            logger.warning(f"Transcription error: {user_text}")
            # Try to generate fallback audio
            try:
                fallback_url = fallback_tts("I'm having trouble understanding your voice right now. Please check your API configuration.")
                return ChatResponse(audio_urls=[fallback_url], transcript="", llm_response=user_text, error=user_text)
            except Exception as fallback_err:
                logger.error(f"Fallback TTS failed: {fallback_err}")
                return ChatResponse(audio_urls=["/fallback.wav"], transcript="", llm_response=user_text, error=user_text)

        logger.info(f"Transcription successful: '{user_text}'")

    except Exception as e:
        logger.error(f"Audio processing error: {e}")
        fallback_text = "I'm having trouble understanding your voice right now. Please try speaking more clearly."
        try:
            audio_url = fallback_tts(fallback_text)
            return ChatResponse(audio_urls=[audio_url], transcript="", llm_response=fallback_text, error=f"Audio processing error: {str(e)}")
        except Exception as fallback_err:
            logger.error(f"Fallback TTS failed: {fallback_err}")
            return ChatResponse(audio_urls=["/fallback.wav"], transcript="", llm_response=fallback_text, error=f"Audio processing error: {str(e)}")

    history = CHAT_SESSIONS.get(session_id, [])
    history.append({"role": "user", "content": user_text})

    # Get persona from session or use default
    persona = CHAT_SESSIONS.get(f"{session_id}_persona", "default")

    try:
        llm_text = generate_llm_response(history, persona)
        if not llm_text:
            raise Exception("Empty response from LLM")

        # Check if LLM returned an error message
        if "API key not configured" in llm_text or "error" in llm_text.lower():
            logger.warning(f"LLM error: {llm_text}")
            fallback_text = "I'm having trouble thinking of a response right now. Please check your API configuration."
            try:
                audio_url = fallback_tts(fallback_text)
                return ChatResponse(audio_urls=[audio_url], transcript=user_text, llm_response=fallback_text, error=llm_text)
            except Exception as fallback_err:
                logger.error(f"Fallback TTS failed: {fallback_err}")
                return ChatResponse(audio_urls=["/fallback.wav"], transcript=user_text, llm_response=fallback_text, error=llm_text)

        logger.info(f"LLM response generated: '{llm_text[:100]}...'" )
    except Exception as e:
        logger.error(f"LLM API error: {e}")
        fallback_text = "I'm having trouble thinking of a response right now."
        try:
            audio_url = fallback_tts(fallback_text)
            return ChatResponse(audio_urls=[audio_url], transcript=user_text, llm_response=fallback_text, error=f"LLM API error: {str(e)}")
        except Exception as fallback_err:
            logger.error(f"Fallback TTS failed: {fallback_err}")
            return ChatResponse(audio_urls=["/fallback.wav"], transcript=user_text, llm_response=fallback_text, error=f"LLM API error: {str(e)}")

    history.append({"role": "model", "content": llm_text})
    CHAT_SESSIONS[session_id] = history

    # Split long LLM text into chunks for TTS
    def split_text(s, n):
        return [s[i:i+n] for i in range(0, len(s), n)]

    audio_urls = []
    try:
        for chunk in split_text(llm_text, 3000):
            if chunk.strip():
                audio_url = murf_tts(chunk)
                if audio_url:
                    audio_urls.append(audio_url)
                    logger.info(f"TTS chunk generated: {audio_url}")
                else:
                    logger.warning("TTS returned no audio URL, using fallback")
                    # Try fallback TTS
                    fallback_url = fallback_tts(chunk)
                    if fallback_url:
                        audio_urls.append(fallback_url)
                    else:
                        raise Exception("Both Murf and fallback TTS failed")
    except Exception as e:
        logger.error(f"TTS error: {e}")
        try:
            fallback_url = fallback_tts("I'm having trouble speaking right now.")
            if fallback_url:
                audio_urls.append(fallback_url)
            else:
                audio_urls.append("/fallback.wav")
            return ChatResponse(audio_urls=audio_urls, transcript=user_text, llm_response=llm_text, error=f"TTS error: {str(e)}")
        except Exception as fallback_err:
            logger.error(f"Fallback TTS failed: {fallback_err}")
            audio_urls = ["/fallback.wav"]
            return ChatResponse(audio_urls=audio_urls, transcript=user_text, llm_response=llm_text, error=f"TTS error: {str(e)}")

    if not audio_urls:
        logger.warning("No audio URLs generated, using fallback")
        try:
            fallback_url = fallback_tts("Here's my response.")
            if fallback_url:
                audio_urls = [fallback_url]
            else:
                audio_urls = ["/fallback.wav"]
        except Exception:
            audio_urls = ["/fallback.wav"]

    logger.info(f"Chat response complete. Audio URLs: {len(audio_urls)}, Transcript: '{user_text}', LLM: '{llm_text[:100]}...'" )
    return ChatResponse(audio_urls=audio_urls, transcript=user_text, llm_response=llm_text)

# Set persona for session
@app.post("/persona/{session_id}/{persona_name}")
async def set_persona(session_id: str, persona_name: str):
    """Set persona for a session"""
    valid_personas = ["default", "pirate", "robot", "cowboy"]
    if persona_name not in valid_personas:
        raise HTTPException(status_code=400, detail=f"Invalid persona. Valid options: {valid_personas}")

    CHAT_SESSIONS[f"{session_id}_persona"] = persona_name
    logger.info(f"Persona for session {session_id} set to {persona_name}")
    return JSONResponse(content={"message": f"Persona set to {persona_name}", "persona": persona_name})

# Get current persona for session
@app.get("/persona/{session_id}")
async def get_persona(session_id: str):
    """Get current persona for a session"""
    persona = CHAT_SESSIONS.get(f"{session_id}_persona", "default")
    return JSONResponse(content={"session_id": session_id, "persona": persona})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "AI Voice Agent is running"}

@app.get("/test-transcription")
async def test_transcription():
    """Test endpoint to check transcription service"""
    try:
        # Test if AssemblyAI is configured
        from services.stt import ASSEMBLYAI_API_KEY
        assemblyai_configured = bool(ASSEMBLYAI_API_KEY and ASSEMBLYAI_API_KEY != "your_assemblyai_api_key_here")

        # Test if Murf is configured - check environment variable directly
        murf_api_key = os.getenv("MURF_API_KEY")
        murf_configured = bool(murf_api_key and murf_api_key != "your_murf_api_key_here")

        # Test if Gemini is configured
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        gemini_configured = bool(gemini_api_key and gemini_api_key != "your_gemini_api_key_here")

        return {
            "status": "ok",
            "message": "Configuration check completed",
            "assemblyai": "configured" if assemblyai_configured else "missing",
            "murf": "configured" if murf_configured else "missing",
            "gemini": "configured" if gemini_configured else "missing"
        }
    except Exception as e:
        return {"status": "error", "message": f"Configuration check failed: {str(e)}"}
