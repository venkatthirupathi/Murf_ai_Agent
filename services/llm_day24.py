import os
import json
import google.generativeai as genai
from typing import AsyncGenerator, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Check if API key is configured
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Persona system prompts for Day 24: Agent Persona
PERSONA_PROMPTS = {
    "default": "You are a helpful and friendly AI assistant. Respond naturally and conversationally.",
    "pirate": "You are a pirate captain! Speak like a pirate with nautical terms. Use phrases like 'Arrr!', 'Shiver me timbers!', 'Ahoy matey!', and talk about treasure, ships, and the seven seas. Keep it fun and engaging!",
    "robot": "You are a sophisticated AI robot. Speak in a precise, mechanical manner. Use robotic language like 'BEEP-BOOP', 'PROCESSING', 'CALCULATING'. Be logical and efficient in your responses.",
    "cowboy": "You are a cowboy from the Wild West! Use western slang like 'Howdy partner!', 'Yeehaw!', 'This town ain't big enough...'. Talk about horses, saloons, and the frontier spirit."
}

def generate_llm_response(history, persona="default"):
    """Generate LLM response using Google Gemini with persona"""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        logger.error("GEMINI_API_KEY not configured or using placeholder")
        return "API key not configured. Please add your Google Gemini API key to the .env file."

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Format conversation history for Gemini with persona system prompt
        conversation = []

        # Add persona system prompt as the first message
        system_prompt = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS["default"])
        conversation.append({"role": "user", "parts": [f"System: {system_prompt}"]})

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

        response = chat.send_message(prompt)
        return response.text
    except Exception as e:
        logger.error(f"LLM API error: {e}")
        return f"AI response error: {str(e)}"

async def generate_streaming_response(history, persona="default") -> AsyncGenerator[str, None]:
    """Generate streaming LLM response with persona"""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
        logger.error("GEMINI_API_KEY not configured or using placeholder")
        yield "API key not configured. Please add your Google Gemini API key to the .env file."
        return

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Format conversation history for Gemini with persona system prompt
        conversation = []

        # Add persona system prompt as the first message
        system_prompt = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS["default"])
        conversation.append({"role": "user", "parts": [f"System: {system_prompt}"]})

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
