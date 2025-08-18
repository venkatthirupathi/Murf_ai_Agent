import os
import asyncio
import logging
import json
import time
from typing import AsyncGenerator
from queue import Queue, Empty
import assemblyai as aai
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
                return ChatResponse(audio_urls=["/fallback.wav"], transcript=user_text, llm_response=fallback_text, error=llm_text)
        
        logger.info(f"LLM response generated: '{llm_text[:100]}...'")
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
            llm_accum = ""
            async for chunk in generate_streaming_response(history):
                if chunk.strip():
                    llm_accum += chunk
                    yield json.dumps({"type": "llm_chunk", "content": chunk}) + "\n"
            
            # Generate TTS for the complete response
            llm_text = llm_accum
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
    
    # Create session-specific upload directory
    session_upload_dir = os.path.join(UPLOAD_DIRECTORY, f"session_{session_id}")
    os.makedirs(session_upload_dir, exist_ok=True)
    
    # File to save streaming audio data (only if we receive containerized formats like webm)
    audio_file_path = os.path.join(session_upload_dir, f"streaming_audio_{int(time.time())}.bin")
    audio_file = None

    # Realtime transcription setup
    transcripts_queue = Queue()
    audio_input_queue = Queue()
    transcriber = None
    aa_streaming_client = None
    aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY", "")
    if not aai.settings.api_key:
        logger.warning("ASSEMBLYAI_API_KEY missing - realtime transcription disabled for this session")
    
    try:
        # Open file for writing binary audio data
        audio_file = open(audio_file_path, 'wb')
        logger.info(f"Started streaming audio recording to: {audio_file_path}")
        
        # Send confirmation that we're ready to receive audio
        await websocket.send_text(json.dumps({
            "type": "ready",
            "message": "Ready to receive streaming audio"
        }))
        
        # Initialize AssemblyAI universal streaming client if configured
        if aai.settings.api_key:
            try:
                from assemblyai.streaming.v3 import (
                    StreamingClient,
                    StreamingClientOptions,
                    StreamingEvents,
                    StreamingParameters,
                    StreamingSessionParameters,
                    BeginEvent,
                    TurnEvent,
                    TerminationEvent,
                    StreamingError,
                )

                options = StreamingClientOptions(api_key=aai.settings.api_key)
                aa_streaming_client = StreamingClient(options)

                def on_begin(self, event: BeginEvent):
                    logger.info(f"AAI streaming session started: {event.id}")

                def on_turn(self, event: TurnEvent):
                    try:
                        text = event.transcript or ""
                        if not text:
                            return
                        is_final = bool(getattr(event, "end_of_turn", False))
                        if is_final:
                            logger.info(f"[AAI Final] {text}")
                        else:
                            logger.info(f"[AAI Partial] {text}")
                        transcripts_queue.put_nowait(json.dumps({
                            "type": "transcript",
                            "final": is_final,
                            "content": text
                        }))
                    except Exception as cb_err:
                        logger.error(f"Error handling AAI turn: {cb_err}")

                def on_terminated(self, event: TerminationEvent):
                    logger.info("AAI streaming session terminated")

                def on_error(self, error: StreamingError):
                    try:
                        logger.error(f"AssemblyAI streaming error: {error}")
                        transcripts_queue.put_nowait(json.dumps({"type": "error", "message": str(error)}))
                    except Exception:
                        pass

                aa_streaming_client.on(StreamingEvents.Begin, on_begin)
                aa_streaming_client.on(StreamingEvents.Turn, on_turn)
                aa_streaming_client.on(StreamingEvents.Termination, on_terminated)
                aa_streaming_client.on(StreamingEvents.Error, on_error)

                # Connect session
                aa_streaming_client.connect(
                    StreamingParameters(
                        sample_rate=16000,
                        format_turns=False,
                    )
                )

                # Background streaming thread that feeds PCM from queue
                def pcm_generator():
                    try:
                        while True:
                            chunk = audio_input_queue.get()
                            if chunk is None:
                                break
                            if chunk:
                                yield chunk
                    except Exception as gerr:
                        logger.error(f"PCM generator error: {gerr}")

                loop = asyncio.get_event_loop()
                _ = loop.run_in_executor(None, lambda: aa_streaming_client.stream(pcm_generator()))
                logger.info("Connected to AssemblyAI Realtime API (universal streaming)")
            except Exception as conn_err:
                logger.error(f"Failed to initialize AssemblyAI streaming: {conn_err}")
                aa_streaming_client = None

        while True:
            # Receive data (text control messages or binary audio)
            message = await websocket.receive()
            if 'bytes' in message and message['bytes'] is not None:
                data = message['bytes']
                if len(data) == 0:
                    # Drain any pending transcripts even if no data
                    try:
                        while True:
                            pending = transcripts_queue.get_nowait()
                            await websocket.send_text(pending)
                    except Empty:
                        pass
                    continue

                try:
                    # Save the audio data to file (raw binary stream)
                    audio_file.write(data)
                    audio_file.flush()

                    # Forward to realtime transcriber via queue (expects PCM16 @ 16k mono)
                    if aa_streaming_client is not None:
                        audio_input_queue.put_nowait(data)

                    # Send confirmation that audio chunk was received
                    await websocket.send_text(json.dumps({
                        "type": "audio_received",
                        "bytes_received": len(data),
                        "total_file_size": audio_file.tell()
                    }))

                    # Drain and forward any pending transcripts
                    try:
                        while True:
                            pending = transcripts_queue.get_nowait()
                            await websocket.send_text(pending)
                    except Empty:
                        pass

                    logger.info(f"Received audio chunk: {len(data)} bytes, total: {audio_file.tell()} bytes")

                except Exception as e:
                    logger.error(f"Error handling audio data: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Error handling audio: {str(e)}"
                    }))
            elif 'text' in message and message['text'] is not None:
                # Handle simple control messages if needed
                try:
                    payload = message['text']
                    logger.info(f"Control message: {payload}")
                    # Optionally acknowledge
                    await websocket.send_text(json.dumps({"type": "ack", "message": payload}))
                except Exception:
                    pass
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"WebSocket error: {str(e)}"
        }))
    finally:
        # Close the audio file
        if audio_file:
            audio_file.close()
            logger.info(f"Finished streaming audio recording: {audio_file_path}")
        # Close realtime transcriber
        try:
            if aa_streaming_client is not None:
                try:
                    audio_input_queue.put_nowait(None)
                except Exception:
                    pass
                try:
                    aa_streaming_client.disconnect(terminate=True)
                except Exception:
                    aa_streaming_client.disconnect()
                logger.info("Closed AssemblyAI streaming connection")
        except Exception as cerr:
            logger.warning(f"Error closing AAI transcriber: {cerr}")
        
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

@app.get("/recorded-audio/{session_id}")
async def list_recorded_audio(session_id: str):
    """List recorded audio files for a session"""
    try:
        session_upload_dir = os.path.join(UPLOAD_DIRECTORY, f"session_{session_id}")
        if not os.path.exists(session_upload_dir):
            return {"session_id": session_id, "files": [], "message": "No recordings found for this session"}
        
        files = []
        for filename in os.listdir(session_upload_dir):
            if filename.endswith('.webm') or filename.endswith('.bin'):
                file_path = os.path.join(session_upload_dir, filename)
                file_size = os.path.getsize(file_path)
                files.append({
                    "filename": filename,
                    "size_bytes": file_size,
                    "size_mb": round(file_size / (1024 * 1024), 2)
                })
        
        return {
            "session_id": session_id,
            "files": files,
            "total_files": len(files),
            "upload_directory": session_upload_dir
        }
    except Exception as e:
        logger.error(f"Error listing recorded audio: {e}")
        return {"error": str(e)}

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
