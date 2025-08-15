import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def generate_llm_response(history):
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
