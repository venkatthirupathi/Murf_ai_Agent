import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Path
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import assemblyai as aai
import google.generativeai as genai

# ---- Global chat history dictionary ----
CHAT_SESSIONS = {}  # {session_id: [{"role":"user", "content":"..."} ...]}

# --- Load environment variables ---
load_dotenv()

# --- API Keys ---
MURF_API_KEY = os.getenv("MURF_API_KEY")
MURF_TTS_ENDPOINT = "https://api.murf.ai/v1/speech/generate-with-key"
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Configure APIs ---
aai.settings.api_key = ASSEMBLYAI_API_KEY
transcriber = aai.Transcriber()
genai.configure(api_key=GEMINI_API_KEY)

# --- Uploads directory ---
UPLOAD_DIRECTORY = "uploads"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

# --- FastAPI App ---
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ----- Helper: Murf fallback audio -----
def generate_fallback_audio(text="I'm having trouble connecting right now."):
    headers = {"api-key": MURF_API_KEY, "Content-Type": "application/json"}
    payload = {"voiceId": "en-US-marcus", "text": text, "format": "mp3"}
    try:
        resp = requests.post(MURF_TTS_ENDPOINT, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data.get("audioFile")
    except Exception:
        # If Murf is also down, serve a static file from /static/
        return "/static/fallback.mp3"

# ----- Text-to-Speech from typed text -----
class SpeechRequest(BaseModel):
    text: str

@app.post("/generate-audio")
def generate_audio(request: SpeechRequest):
    input_text = request.text.strip()
    if not input_text:
        raise HTTPException(status_code=400, detail="Input text cannot be empty")

    headers = {"api-key": MURF_API_KEY, "Content-Type": "application/json"}
    payload = {"voiceId": "en-US-marcus", "text": input_text, "format": "mp3"}
    try:
        response = requests.post(MURF_TTS_ENDPOINT, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception as err:
        fallback_url = generate_fallback_audio()
        return JSONResponse({"audio_url": fallback_url, "error": str(err)})

    audio_url = data.get("audioFile")
    if not audio_url:
        fallback_url = generate_fallback_audio()
        return JSONResponse({"audio_url": fallback_url, "error": "No audio URL from Murf"})
    return {"audio_url": audio_url}

# ----- Conversational endpoint with chat history -----
@app.post("/agent/chat/{session_id}")
async def agent_chat(session_id: str = Path(...), file: UploadFile = File(...)):
    # 1. Read audio
    audio_data = await file.read()

    # 2. Transcribe with AssemblyAI
    try:
        transcript = transcriber.transcribe(audio_data)
        user_text = transcript.text
        if not user_text:
            raise Exception("Empty transcription result")
    except Exception as e:
        fallback_text = "I'm having trouble connecting right now."
        audio_url = generate_fallback_audio(fallback_text)
        return JSONResponse({
            "audio_urls": [audio_url],
            "transcript": "",
            "llm_response": fallback_text,
            "error": f"AssemblyAI error: {str(e)}"
        })

    # 3. Get existing history or start new one
    history = CHAT_SESSIONS.get(session_id, [])
    history.append({"role": "user", "content": user_text})

    # 4. Call Gemini LLM with full formatted history
    try:
        formatted_history = [
            {"role": msg["role"], "parts": [{"text": msg["content"]}]}
            for msg in history
        ]
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(formatted_history)
        llm_text = response.text
    except Exception as e:
        fallback_text = "I'm having trouble connecting right now."
        audio_url = generate_fallback_audio(fallback_text)
        return JSONResponse({
            "audio_urls": [audio_url],
            "transcript": user_text,
            "llm_response": fallback_text,
            "error": f"Gemini API error: {str(e)}"
        })

    # 5. Append bot reply to history
    history.append({"role": "model", "content": llm_text})
    CHAT_SESSIONS[session_id] = history

    # 6. Convert LLM text to speech with Murf TTS
    def split_text(s, n): return [s[i:i+n] for i in range(0, len(s), n)]
    audio_urls = []
    try:
        headers = {"api-key": MURF_API_KEY, "Content-Type": "application/json"}
        for chunk in split_text(llm_text, 3000):
            payload = {"voiceId": "en-US-marcus", "text": chunk, "format": "mp3"}
            resp = requests.post(MURF_TTS_ENDPOINT, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            audio_url = data.get("audioFile")
            if audio_url:
                audio_urls.append(audio_url)
            else:
                raise Exception("No audio URL from Murf")
    except Exception as e:
        fallback_url = generate_fallback_audio()
        return JSONResponse({
            "audio_urls": [fallback_url],
            "transcript": user_text,
            "llm_response": llm_text,
            "error": f"Murf API error: {str(e)}"
        })

    # 7. Return final response
    return JSONResponse({
        "audio_urls": audio_urls,
        "transcript": user_text,
        "llm_response": llm_text
    })
