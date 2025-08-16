import os
import logging
import json
from typing import AsyncGenerator
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Path, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from schemas.audio import SpeechRequest, SpeechResponse
from schemas.chat import ChatResponse, StreamingChatResponse

from services.tts import murf_tts, fallback_tts
from services.stt import transcribe_audio
from services.llm import generate_llm_response, generate_streaming_response

load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHAT_SESSIONS = {}
WEBSOCKET_CONNECTIONS = {}

UPLOAD_DIRECTORY = "uploads"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

# Validate required environment variables
required_env_vars = ["MURF_API_KEY", "ASSEMBLYAI_API_KEY", "GEMINI_API_KEY"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    logger.warning(f"Missing environment variables: {missing_vars}")

app = FastAPI(title="AI Voice Agent", description="Voice-first conversational AI agent with streaming")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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
            return SpeechResponse(audio_url="/static/fallback.mp3", error=str(err))

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
                return ChatResponse(audio_urls=["/static/fallback.mp3"], transcript="", llm_response=user_text, error=user_text)
        
        logger.info(f"Transcription successful: '{user_text}'")
        
    except Exception as e:
        logger.error(f"Audio processing error: {e}")
        fallback_text = "I'm having trouble understanding your voice right now. Please try speaking more clearly."
        try:
            audio_url = fallback_tts(fallback_text)
            return ChatResponse(audio_urls=[audio_url], transcript="", llm_response=fallback_text, error=f"Audio processing error: {str(e)}")
        except Exception as fallback_err:
            logger.error(f"Fallback TTS failed: {fallback_err}")
            return ChatResponse(audio_urls=["/static/fallback.mp3"], transcript="", llm_response=fallback_text, error=f"Audio processing error: {str(e)}")

    history = CHAT_SESSIONS.get(session_id, [])
    history.append({"role": "user", "content": user_text})

    try:
        llm_text = generate_llm_response(history)
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
                return ChatResponse(audio_urls=["/static/fallback.mp3"], transcript=user_text, llm_response=fallback_text, error=llm_text)
        
        logger.info(f"LLM response generated: '{llm_text[:100]}...'")
    except Exception as e:
        logger.error(f"LLM API error: {e}")
        fallback_text = "I'm having trouble thinking of a response right now."
        try:
            audio_url = fallback_tts(fallback_text)
            return ChatResponse(audio_urls=[audio_url], transcript=user_text, llm_response=fallback_text, error=f"LLM API error: {str(e)}")
        except Exception as fallback_err:
            logger.error(f"Fallback TTS failed: {fallback_err}")
            return ChatResponse(audio_urls=["/static/fallback.mp3"], transcript=user_text, llm_response=fallback_text, error=f"LLM API error: {str(e)}")

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
                audio_urls.append("/static/fallback.mp3")
            return ChatResponse(audio_urls=audio_urls, transcript=user_text, llm_response=llm_text, error=f"TTS error: {str(e)}")
        except Exception as fallback_err:
            logger.error(f"Fallback TTS failed: {fallback_err}")
            audio_urls = ["/static/fallback.mp3"]
            return ChatResponse(audio_urls=audio_urls, transcript=user_text, llm_response=llm_text, error=f"TTS error: {str(e)}")

    if not audio_urls:
        logger.warning("No audio URLs generated, using fallback")
        try:
            fallback_url = fallback_tts("Here's my response.")
            if fallback_url:
                audio_urls = [fallback_url]
            else:
                audio_urls = ["/static/fallback.mp3"]
        except Exception:
            audio_urls = ["/static/fallback.mp3"]

    logger.info(f"Chat response complete. Audio URLs: {len(audio_urls)}, Transcript: '{user_text}', LLM: '{llm_text[:100]}...'")
    return ChatResponse(audio_urls=audio_urls, transcript=user_text, llm_response=llm_text)

# NEW: Streaming chat endpoint
@app.post("/agent/chat/{session_id}/stream")
async def agent_chat_stream(session_id: str = Path(...), file: UploadFile = File(...)):
    """Streaming chat endpoint that returns real-time responses"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")
    
    if not file.content_type or not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    try:
        audio_data = await file.read()
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        logger.info(f"Streaming chat - Received audio file: {file.filename}, size: {len(audio_data)} bytes")
        
        user_text = transcribe_audio(audio_data)
        if not user_text:
            raise Exception("Speech could not be understood. Please try speaking more clearly.")
        
        logger.info(f"Streaming chat - Transcription successful: '{user_text}'")
        
    except Exception as e:
        logger.error(f"Streaming chat - Audio processing error: {e}")
        fallback_text = "I'm having trouble understanding your voice right now. Please try speaking more clearly."
        return StreamingResponse(
            iter([json.dumps({"type": "error", "message": fallback_text}) + "\n"]),
            media_type="text/plain"
        )

    history = CHAT_SESSIONS.get(session_id, [])
    history.append({"role": "user", "content": user_text})

    async def generate_stream():
        try:
            # Stream LLM response
            async for chunk in generate_streaming_response(history):
                if chunk.strip():
                    yield json.dumps({"type": "llm_chunk", "content": chunk}) + "\n"
            
            # Generate TTS for the complete response
            llm_text = "".join([msg["content"] for msg in history if msg["role"] == "model"])
            if llm_text:
                try:
                    audio_url = murf_tts(llm_text)
                    if audio_url:
                        yield json.dumps({"type": "audio_ready", "audio_url": audio_url}) + "\n"
                    else:
                        yield json.dumps({"type": "error", "message": "Failed to generate audio"}) + "\n"
                except Exception as e:
                    logger.error(f"TTS error in streaming: {e}")
                    yield json.dumps({"type": "error", "message": "Failed to generate audio"}) + "\n"
            
            # Update session history
            history.append({"role": "model", "content": llm_text})
            CHAT_SESSIONS[session_id] = history
            
            yield json.dumps({"type": "complete"}) + "\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    return StreamingResponse(generate_stream(), media_type="text/plain")

# NEW: WebSocket endpoint for real-time streaming
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    WEBSOCKET_CONNECTIONS[session_id] = websocket
    
    try:
        while True:
            # Wait for audio data from client
            data = await websocket.receive_bytes()
            
            if len(data) == 0:
                continue
                
            try:
                # Transcribe audio
                user_text = transcribe_audio(data)
                if not user_text:
                    await websocket.send_text(json.dumps({
                        "type": "error", 
                        "message": "Speech could not be understood. Please try speaking more clearly."
                    }))
                    continue
                
                # Update session history
                history = CHAT_SESSIONS.get(session_id, [])
                history.append({"role": "user", "content": user_text})
                
                # Send user transcript
                await websocket.send_text(json.dumps({
                    "type": "transcript",
                    "content": user_text
                }))
                
                # Stream LLM response
                llm_text = ""
                async for chunk in generate_streaming_response(history):
                    if chunk.strip():
                        llm_text += chunk
                        await websocket.send_text(json.dumps({
                            "type": "llm_chunk",
                            "content": chunk
                        }))
                
                # Generate TTS
                if llm_text:
                    try:
                        audio_url = murf_tts(llm_text)
                        if audio_url:
                            await websocket.send_text(json.dumps({
                                "type": "audio_ready",
                                "audio_url": audio_url
                            }))
                    except Exception as e:
                        logger.error(f"TTS error in WebSocket: {e}")
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Failed to generate audio"
                        }))
                
                # Update session history
                history.append({"role": "model", "content": llm_text})
                CHAT_SESSIONS[session_id] = history
                
                await websocket.send_text(json.dumps({"type": "complete"}))
                
            except Exception as e:
                logger.error(f"WebSocket processing error: {e}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Processing error: {str(e)}"
                }))
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    finally:
        if session_id in WEBSOCKET_CONNECTIONS:
            del WEBSOCKET_CONNECTIONS[session_id]

# NEW: Get conversation history
@app.get("/conversation/{session_id}")
async def get_conversation(session_id: str):
    """Get conversation history for a session"""
    history = CHAT_SESSIONS.get(session_id, [])
    return {"session_id": session_id, "history": history}

# NEW: Clear conversation history
@app.delete("/conversation/{session_id}")
async def clear_conversation(session_id: str):
    """Clear conversation history for a session"""
    if session_id in CHAT_SESSIONS:
        del CHAT_SESSIONS[session_id]
    return {"message": "Conversation cleared"}

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
        if not ASSEMBLYAI_API_KEY:
            return {"status": "error", "message": "AssemblyAI API key not configured"}
        
        # Test if Murf is configured
        from services.tts import MURF_API_KEY
        if not MURF_API_KEY:
            return {"status": "error", "message": "Murf API key not configured"}
        
        # Test if Gemini is configured
        from services.llm import genai
        if not os.getenv("GEMINI_API_KEY"):
            return {"status": "error", "message": "Gemini API key not configured"}
        
        return {
            "status": "ok", 
            "message": "All services configured",
            "assemblyai": "configured" if ASSEMBLYAI_API_KEY else "missing",
            "murf": "configured" if MURF_API_KEY else "missing",
            "gemini": "configured" if os.getenv("GEMINI_API_KEY") else "missing"
        }
    except Exception as e:
        return {"status": "error", "message": f"Configuration check failed: {str(e)}"}
