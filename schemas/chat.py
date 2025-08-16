from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    session_id: str

class ChatResponse(BaseModel):
    audio_urls: List[str]
    transcript: str
    llm_response: str
    error: Optional[str] = None

class StreamingChatResponse(BaseModel):
    type: str  # "llm_chunk", "audio_ready", "complete", "error"
    content: Optional[str] = None
    audio_url: Optional[str] = None
    message: Optional[str] = None
