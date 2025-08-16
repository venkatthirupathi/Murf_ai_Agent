import os
import google.generativeai as genai
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)

# Check if API key is configured
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def generate_llm_response(history):
    """Generate LLM response using Google Gemini"""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        logger.error("GEMINI_API_KEY not configured or using placeholder")
        return "API key not configured. Please add your Google Gemini API key to the .env file."
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Format conversation history for Gemini
        conversation = []
        for message in history:
            if message["role"] == "user":
                conversation.append({"role": "user", "parts": [message["content"]]})
            elif message["role"] == "model":
                conversation.append({"role": "model", "parts": [message["content"]]})
        
        # Start chat session with prior messages
        chat = model.start_chat(history=conversation)
        
        # Send the latest user message (fallback to a generic prompt if missing)
        latest_user_text = ""
        for m in reversed(history):
            if m.get("role") == "user":
                latest_user_text = m.get("content", "").strip()
                break
        prompt = latest_user_text or "Please respond naturally to the user's last message."
        
        response = chat.send_message(prompt)
        return response.text
    except Exception as e:
        logger.error(f"LLM API error: {e}")
        return f"AI response error: {str(e)}"

async def generate_streaming_response(history) -> AsyncGenerator[str, None]:
    """Generate streaming LLM response"""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        logger.error("GEMINI_API_KEY not configured or using placeholder")
        yield "API key not configured. Please add your Google Gemini API key to the .env file."
        return
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Format conversation history for Gemini
        conversation = []
        for message in history:
            if message["role"] == "user":
                conversation.append({"role": "user", "parts": [message["content"]]})
            elif message["role"] == "model":
                conversation.append({"role": "model", "parts": [message["content"]]})
        
        # Start chat session with prior messages
        chat = model.start_chat(history=conversation)
        
        # Send the latest user message
        latest_user_text = ""
        for m in reversed(history):
            if m.get("role") == "user":
                latest_user_text = m.get("content", "").strip()
                break
        prompt = latest_user_text or "Please respond naturally to the user's last message."
        
        # Stream the response
        response = chat.send_message(prompt, stream=True)
        
        for chunk in response:
            if chunk.text:
                yield chunk.text
                
    except Exception as e:
        logger.error(f"Streaming LLM error: {e}")
        yield f"Error generating response: {str(e)}"
