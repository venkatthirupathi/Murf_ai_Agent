import os
import requests
import logging
import json
import asyncio
import time
from typing import AsyncGenerator, Optional
import base64
import io
import wave

try:
    import websockets
except Exception:  # pragma: no cover
    websockets = None

logger = logging.getLogger(__name__)

def get_murf_api_key() -> Optional[str]:
    """Fetch Murf API key at call time so .env loaded later is respected."""
    return os.getenv("MURF_API_KEY")
MURF_TTS_ENDPOINT = "https://api.murf.ai/v1/speech/generate-with-key"
MURF_WS_URL = os.getenv("MURF_WS_URL", "wss://api.murf.ai/v1/speech/stream-input")
MURF_WS_CONTEXT_ID = os.getenv("MURF_WS_CONTEXT_ID", "day20-static-context")

def murf_tts(text):
    """Generate TTS using Murf AI API"""
    api_key = get_murf_api_key()
    if not api_key or api_key == "your_murf_api_key_here":
        logger.warning("MURF_API_KEY not configured or using placeholder")
        return None
    
    try:
        headers = {"api-key": api_key, "Content-Type": "application/json"}
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
        api_key = get_murf_api_key()
        if api_key and api_key != "your_murf_api_key_here":
            result = murf_tts(text)
            if result:
                return result
    except Exception as e:
        logger.error(f"Fallback TTS failed: {e}")
    
    # Return fallback audio file path
    return "/fallback.wav"


class MurfWsTTSStreamer:
    """Murf WebSocket TTS streamer that sends base64 audio chunks to client via WebSocket.

    Usage:
        streamer = MurfWsTTSStreamer(websocket=websocket_connection)
        await streamer.connect()
        await streamer.send_text_chunk("Hello ")
        await streamer.send_text_chunk("world!")
        await streamer.finish()
        await streamer.close()
    """

    def __init__(self,
                 voice_id: str = os.getenv("MURF_VOICE_ID", "en-US-marcus"),
                 sample_rate: int = int(os.getenv("MURF_WS_SAMPLE_RATE", "24000")),
                 channel_type: str = os.getenv("MURF_WS_CHANNEL", "MONO"),
                 audio_format: str = os.getenv("MURF_WS_FORMAT", "WAV"),
                 context_id: str = MURF_WS_CONTEXT_ID,
                 websocket=None) -> None:
        self.voice_id = voice_id
        self.sample_rate = sample_rate
        self.channel_type = channel_type
        self.audio_format = audio_format
        self.context_id = context_id
        self.websocket = websocket  # WebSocket connection to send audio chunks to client
        self._ws = None
        self._receiver_task: Optional[asyncio.Task] = None
        self._closed = False
        self._enabled = True

    async def connect(self) -> None:
        # Gracefully disable WS if not configured
        api_key = get_murf_api_key()
        if not api_key or api_key == "your_murf_api_key_here":
            logger.error("MURF_API_KEY not configured for WebSocket streaming - Murf WS disabled")
            self._enabled = False
            return
        if websockets is None:
            logger.error("'websockets' package not available - Murf WS disabled")
            self._enabled = False
            return

        url = (
            f"{MURF_WS_URL}?api-key={api_key}"
            f"&sample_rate={self.sample_rate}&channel_type={self.channel_type}&format={self.audio_format}"
        )
        logger.info(f"Connecting to Murf WS: {url}")
        self._ws = await websockets.connect(url, max_size=None)

        # Send voice configuration
        voice_config = {
            "voice_config": {
                "voiceId": self.voice_id,
                # Optional tunables; keep neutral to avoid surprises
                "rate": 0,
                "pitch": 0,
                "variation": 1
            }
        }
        await self._ws.send(json.dumps(voice_config))

        # Start receiver loop
        loop = asyncio.get_event_loop()
        self._receiver_task = loop.create_task(self._receiver())

    async def _receiver(self) -> None:
        try:
            while True:
                msg = await self._ws.recv()
                try:
                    data = json.loads(msg)
                except Exception:
                    logger.debug("Non-JSON message from Murf WS; ignoring")
                    continue

                # Print base64 audio chunks to console as required
                if isinstance(data, dict) and "audio" in data:
                    base64_audio = data.get("audio")
                    # Printing to stdout so it shows in console and logs
                    print(f"Murf WS audio chunk (base64): {base64_audio}")
                    logger.info("Received Murf WS audio chunk (base64 logged above)")

                    # Send base64 audio chunk to client via WebSocket if connected
                    if self.websocket:
                        try:
                            await self.websocket.send_text(json.dumps({
                                "type": "audio_chunk",
                                "base64_audio": base64_audio,
                                "timestamp": time.time()
                            }))
                            logger.info("Sent audio chunk to client via WebSocket")
                        except Exception as ws_err:
                            logger.error(f"Failed to send audio chunk to client: {ws_err}")

                # Stop condition if Murf signals final audio
                if data.get("isFinalAudio") is True:
                    logger.info("Murf WS signaled final audio")
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning(f"Murf WS receiver error: {e}")

    async def send_text_chunk(self, text: str) -> None:
        if not text:
            return
        if not self._enabled:
            # Demo fallback: generate short silence WAV and print base64 so user can screenshot
            try:
                buf = io.BytesIO()
                with wave.open(buf, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(self.sample_rate)
                    # ~120ms of silence
                    wf.writeframes(b"\x00\x00" * int(self.sample_rate * 0.12))
                b64 = base64.b64encode(buf.getvalue()).decode('ascii')
                print(f"Murf WS audio chunk (base64): {b64}")
                logger.info("Printed demo base64 audio chunk (Murf WS disabled)")
            except Exception as demo_err:
                logger.debug(f"Demo base64 generation failed: {demo_err}")
            return
        if not self._ws:
            raise RuntimeError("Murf WS not connected")
        payload = {"context_id": self.context_id, "text": text}
        await self._ws.send(json.dumps(payload))

    async def finish(self) -> None:
        if not self._enabled:
            print("Murf WS signaled final audio")
            return
        if not self._ws:
            return
        try:
            await self._ws.send(json.dumps({"context_id": self.context_id, "end": True}))
        except Exception:
            pass

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            await self.finish()
        except Exception:
            pass
        try:
            if self._receiver_task and not self._receiver_task.done():
                self._receiver_task.cancel()
        except Exception:
            pass
        try:
            if self._ws:
                await self._ws.close()
        except Exception:
            pass


async def stream_text_to_murf_ws(text_stream: AsyncGenerator[str, None],
                                 streamer: Optional[MurfWsTTSStreamer] = None) -> None:
    """Convenience function to stream text chunks to Murf WS and print base64 audio.

    Ensures a connection is created and properly closed.
    """
    owned = False
    if streamer is None:
        streamer = MurfWsTTSStreamer()
        owned = True
    try:
        await streamer.connect()
        async for chunk in text_stream:
            if chunk and chunk.strip():
                await streamer.send_text_chunk(chunk)
        await streamer.finish()
    finally:
        if owned:
            await streamer.close()
