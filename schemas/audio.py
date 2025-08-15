from pydantic import BaseModel

class SpeechRequest(BaseModel):
    text: str

class SpeechResponse(BaseModel):
    audio_url: str
    error: str = None  # Optional error field
