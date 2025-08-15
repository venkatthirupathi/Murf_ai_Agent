from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    session_id: str

class ChatResponse(BaseModel):
    audio_urls: List[str]
    transcript: Optional[str]
    llm_response: Optional[str]
    error: Optional[str]
