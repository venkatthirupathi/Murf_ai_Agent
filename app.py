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
from services.web_search import perform_web_search, get_news, get_weather
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from schemas.audio import SpeechRequest, SpeechResponse
from schemas.chat import ChatResponse, StreamingChatResponse
import orjson

from services.tts import murf_tts, fallback_tts, MurfWsTTSStreamer
from services.stt import transcribe_audio
from services.llm import generate_llm_response, generate_streaming_response
from custom_json import custom_json_dumps

load_dotenv()

# Add to your FastAPI backend file (e.g., main.py)
import os
import requests
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()



@app.post("/agent/skill/search")
async def agent_skill_search(request: Request):
    data = await request.json()
    query = data.get("query")
    api_key = os.getenv("TAVILY_API_KEY")
    url = "https://api.tavily.com/search"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"query": query, "max_results": 3}
    response = requests.get(url, headers=headers, params=params)
    return response.json()
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

    # Get persona from session or use default
    persona = CHAT_SESSIONS.get(f"{session_id}_persona", "default")

    async def generate_stream():
        try:
            # Stream LLM response
            llm_accum = ""
            streamer = MurfWsTTSStreamer()

            # Connect to Murf WS once with static context_id; receiver prints base64
            await streamer.connect()
            try:
                async for chunk in generate_streaming_response(history, persona):
                    if chunk.strip():
                        llm_accum += chunk
                        # forward chunk to client UI
                        yield json.dumps({"type": "llm_chunk", "content": chunk}) + "\n"
                        # forward chunk to Murf WS
                        try:
                            await streamer.send_text_chunk(chunk)
                        except Exception as ws_err:
                            logger.error(f"Error sending chunk to Murf WS: {ws_err}")
                # signal end of input to Murf
                await streamer.finish()
            finally:
                await streamer.close()

            # Generate TTS for the complete response (preserve previous behavior/UI)
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
    transcripts_forwarder_task = None
    llm_stream_task = None
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
                        
                        # Check if this is the end of a turn
                        is_final = bool(getattr(event, "end_of_turn", False))
                        
                        if is_final:
                            logger.info(f"[AAI Final Turn] {text}")
                            # Send final transcript
                            transcripts_queue.put_nowait(json.dumps({
                                "type": "transcript",
                                "final": True,
                                "content": text
                            }))
                            # Send turn end notification
                            transcripts_queue.put_nowait(json.dumps({
                                "type": "turn_end",
                                "transcript": text
                            }))
                        else:
                            logger.info(f"[AAI Partial] {text}")
                            # Send partial transcript
                            transcripts_queue.put_nowait(json.dumps({
                                "type": "transcript",
                                "final": False,
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

                # Connect session with turn detection enabled
                aa_streaming_client.connect(
                    StreamingParameters(
                        sample_rate=16000,
                        format_turns=True,  # Enable turn detection
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

                # Helper to stream LLM response after final transcript
                async def stream_llm_from_transcript(final_text: str):
                    nonlocal llm_stream_task
                    try:
                        # Update history with user's final transcript
                        history = CHAT_SESSIONS.get(session_id, [])
                        history.append({"role": "user", "content": final_text})
                        CHAT_SESSIONS[session_id] = history

                        # Get persona from session or use default
                        persona = CHAT_SESSIONS.get(f"{session_id}_persona", "default")
                        logger.info(f"Streaming LLM response with persona: {persona}")

                        # Stream LLM chunks back to client
                        accumulated_text = ""
                        # Create Murf WS streamer to stream chunks as they arrive
                        ws_streamer = MurfWsTTSStreamer(websocket=websocket)
                        await ws_streamer.connect()
                        try:
                            async for chunk in generate_streaming_response(history, persona):
                                if chunk and chunk.strip():
                                    accumulated_text += chunk
                                    try:
                                        await websocket.send_text(json.dumps({
                                            "type": "llm_chunk",
                                            "content": chunk
                                        }))
                                    except Exception as send_err:
                                        logger.error(f"Failed to send llm_chunk over WebSocket: {send_err}")
                                        break
                                    # Also forward chunk to Murf WS; base64 audio gets printed to console
                                    try:
                                        await ws_streamer.send_text_chunk(chunk)
                                    except Exception as ws_err:
                                        logger.error(f"Error sending chunk to Murf WS: {ws_err}")
                        finally:
                            # Signal end to Murf WS
                            try:
                                await ws_streamer.finish()
                            finally:
                                await ws_streamer.close()

                        if accumulated_text:
                            logger.info(f"LLM streamed response: {accumulated_text}")

                            # Generate TTS for the full response
                            try:
                                audio_url = murf_tts(accumulated_text)
                                if audio_url:
                                    await websocket.send_text(json.dumps({
                                        "type": "audio_ready",
                                        "audio_url": audio_url
                                    }))
                                else:
                                    await websocket.send_text(json.dumps({
                                        "type": "error",
                                        "message": "Failed to generate audio"
                                    }))
                            except Exception as tts_err:
                                logger.error(f"TTS error (streaming): {tts_err}")
                                try:
                                    await websocket.send_text(json.dumps({
                                        "type": "error",
                                        "message": "Failed to generate audio"
                                    }))
                                except Exception:
                                    pass

                            # Update history with model response
                            history.append({"role": "model", "content": accumulated_text})
                            CHAT_SESSIONS[session_id] = history

                        try:
                            await websocket.send_text(json.dumps({"type": "complete"}))
                        except Exception:
                            pass
                    except Exception as llm_err:
                        logger.error(f"Streaming LLM error: {llm_err}")
                        try:
                            await websocket.send_text(json.dumps({
                                "type": "error",
                                "message": str(llm_err)
                            }))
                        except Exception:
                            pass

                # Background task to forward transcripts and trigger LLM when turn ends
                async def forward_and_handle_transcripts():
                    nonlocal llm_stream_task
                    try:
                        while True:
                            drained_any = False
                            try:
                                while True:
                                    pending = transcripts_queue.get_nowait()
                                    drained_any = True
                                    # Forward to client
                                    try:
                                        await websocket.send_text(pending)
                                    except Exception as send_err:
                                        logger.error(f"Failed to forward transcript: {send_err}")
                                        break

                                    # Handle turn_end to trigger LLM streaming
                                    try:
                                        payload = json.loads(pending)
                                        if payload.get("type") == "turn_end":
                                            final_text = payload.get("transcript", "")
                                            if final_text:
                                                # Avoid overlapping LLM tasks
                                                if llm_stream_task is None or llm_stream_task.done():
                                                    llm_stream_task = asyncio.create_task(stream_llm_from_transcript(final_text))
                                    except Exception:
                                        pass
                            except Empty:
                                pass
                            # Yield control and avoid tight loop
                            await asyncio.sleep(0.05 if not drained_any else 0)
                    except asyncio.CancelledError:
                        return
                    except Exception as fwd_err:
                        logger.error(f"Transcript forwarder error: {fwd_err}")

                transcripts_forwarder_task = asyncio.create_task(forward_and_handle_transcripts())
            except Exception as conn_err:
                logger.error(f"Failed to initialize AssemblyAI streaming: {conn_err}")
                aa_streaming_client = None

        while True:
            # Receive data (text control messages or binary audio)
            message = await websocket.receive()
            if 'bytes' in message and message['bytes'] is not None:
                data = message['bytes']
                if len(data) == 0:
                    # Background forwarder handles transcript flushing
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

                    # Background forwarder handles transcript flushing

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
        # Cancel transcripts forwarder
        try:
            if transcripts_forwarder_task is not None:
                transcripts_forwarder_task.cancel()
        except Exception:
            pass
        # Cancel any running LLM task
        try:
            if llm_stream_task is not None and not llm_stream_task.done():
                llm_stream_task.cancel()
        except Exception:
            pass
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

# NEW: Set persona for session
@app.post("/persona/{session_id}/{persona_name}")
async def set_persona(session_id: str, persona_name: str):
    """Set persona for a session"""
    valid_personas = ["default", "pirate", "robot", "cowboy"]
    if persona_name not in valid_personas:
        raise HTTPException(status_code=400, detail=f"Invalid persona. Valid options: {valid_personas}")
    
    CHAT_SESSIONS[f"{session_id}_persona"] = persona_name
    logger.info(f"Persona for session {session_id} set to {persona_name}")
    return JSONResponse(content={"message": f"Persona set to {persona_name}", "persona": persona_name})

# NEW: Get current persona for session
@app.get("/persona/{session_id}")
async def get_persona(session_id: str):
    """Get current persona for a session"""
    persona = CHAT_SESSIONS.get(f"{session_id}_persona", "default")
    return JSONResponse(content={"session_id": session_id, "persona": persona})

# Test endpoint to check JSON formatting
@app.get("/test-json")
async def test_json():
    """Test endpoint to check JSON formatting"""
    # Use orjson for proper JSON formatting
    json_response = orjson.dumps({"test": "value", "another": "field"})
    return Response(content=json_response, media_type="application/json")

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

# NEW: Web search endpoint
@app.post("/web-search")
async def web_search(request: Request):
    """Endpoint to perform a web search"""
    try:
        body = await request.json()
        query = body.get("query")
        max_results = body.get("max_results", 3)

        if not query:
            raise HTTPException(status_code=400, detail="Query parameter is required")

        results = perform_web_search(query, max_results)
        if results is None:
            raise HTTPException(status_code=500, detail="Web search service is unavailable")

        return {"results": results}
    except Exception as e:
        logger.error(f"Web search error: {e}")
        raise HTTPException(status_code=500, detail=f"Web search failed: {str(e)}")

@app.post("/agent/skill/web_search")
async def agent_skill_web_search(request: Request):
    """Endpoint to perform a web search as a special skill"""
    try:
        body = await request.json()
        query = body.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter is required")

        results = perform_web_search(query)
        if results is None:
            raise HTTPException(status_code=500, detail="Web search service is unavailable")

        return {"results": results}
    except Exception as e:
        logger.error(f"Agent skill web search error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent skill web search failed: {str(e)}")

@app.post("/agent/skill/news")
async def agent_skill_news(request: Request):
    """Endpoint to get the latest news as a special skill"""
    try:
        body = await request.json()
        topic = body.get("topic", "technology") # Default to technology news
        
        results = get_news(topic)
        if results is None:
            raise HTTPException(status_code=500, detail="News service is unavailable")

        return {"results": results}
    except Exception as e:
        logger.error(f"Agent skill news error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent skill news failed: {str(e)}")

@app.post("/agent/skill/weather")
async def agent_skill_weather(request: Request):
    """Endpoint to get weather information as a special skill"""
    try:
        body = await request.json()
        location = body.get("location")
        if not location:
            raise HTTPException(status_code=400, detail="Location parameter is required")
        
        results = get_weather(location)
        if results is None:
            raise HTTPException(status_code=500, detail="Weather service is unavailable")

        return {"results": results}
    except Exception as e:
        logger.error(f"Agent skill weather error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent skill weather failed: {str(e)}")
