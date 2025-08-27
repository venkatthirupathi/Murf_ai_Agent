import os
import json
import google.generativeai as genai
from typing import AsyncGenerator, List, Dict, Any
import logging
from services.web_search import perform_web_search, get_news, get_weather

logger = logging.getLogger(__name__)

# Check if API key is configured
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Persona system prompts
PERSONA_PROMPTS = {
    "default": "You are a helpful and friendly AI assistant. You have access to web search capabilities that allow you to get the latest information, news, and weather. Use these tools when the user asks for current information or when you need to verify facts. Respond naturally and conversationally.",
    "pirate": "You are a pirate captain! Speak like a pirate with nautical terms. Use phrases like 'Arrr!', 'Shiver me timbers!', 'Ahoy matey!', and talk about treasure, ships, and the seven seas. You have access to web search to find the latest treasure maps and sea conditions! Keep it fun and engaging!",
    "robot": "You are a sophisticated AI robot. Speak in a precise, mechanical manner. Use robotic language like 'BEEP-BOOP', 'PROCESSING', 'CALCULATING'. You have access to web search capabilities for data verification and information retrieval. Be logical and efficient in your responses.",
    "cowboy": "You are a cowboy from the Wild West! Use western slang like 'Howdy partner!', 'Yeehaw!', 'This town ain't big enough...'. Talk about horses, saloons, and the frontier spirit. You can use web search to check weather conditions for cattle drives and find the latest frontier news!"
}

# Function definitions for web search capabilities (Gemini uses a different format)
# For Gemini, we'll use a simpler approach with explicit function calling in the prompt
# since Gemini 1.5 Flash doesn't support the same function calling format as OpenAI

# Function descriptions for the LLM to understand available capabilities
FUNCTION_DESCRIPTIONS = {
    "search_web": "Search the web for current information, news, or facts. Use this when the user asks about recent events, needs up-to-date information, or when you need to verify facts. Parameters: query (required), max_results (optional, default: 3)",
    "get_latest_news": "Get the latest news on a specific topic. Use this when the user asks for recent news or current events. Parameters: topic (optional, default: 'technology'), max_results (optional, default: 5)",
    "get_weather": "Get current weather information for a specific location. Use this when the user asks about weather conditions. Parameters: location (required)"
}

# Function implementations
import os
import json
import google.generativeai as genai
from typing import AsyncGenerator, List, Dict, Any
import logging
from services.web_search import perform_web_search, get_news, get_weather

logger = logging.getLogger(__name__)

# Check if API key is configured
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Persona system prompts
PERSONA_PROMPTS = {
    "default": "You are a helpful and friendly AI assistant. You have access to web search capabilities that allow you to get the latest information, news, and weather. Use these tools when the user asks for current information or when you need to verify facts. Respond naturally and conversationally.",
    "pirate": "You are a pirate captain! Speak like a pirate with nautical terms. Use phrases like 'Arrr!', 'Shiver me timbers!', 'Ahoy matey!', and talk about treasure, ships, and the seven seas. You have access to web search to find the latest treasure maps and sea conditions! Keep it fun and engaging!",
    "robot": "You are a sophisticated AI robot. Speak in a precise, mechanical manner. Use robotic language like 'BEEP-BOOP', 'PROCESSING', 'CALCULATING'. You have access to web search capabilities for data verification and information retrieval. Be logical and efficient in your responses.",
    "cowboy": "You are a cowboy from the Wild West! Use western slang like 'Howdy partner!', 'Yeehaw!', 'This town ain't big enough...'. Talk about horses, saloons, and the frontier spirit. You can use web search to check weather conditions for cattle drives and find the latest frontier news!"
}

# Function definitions for web search capabilities (Gemini uses a different format)
# For Gemini, we'll use a simpler approach with explicit function calling in the prompt
# since Gemini 1.5 Flash doesn't support the same function calling format as OpenAI

# Function descriptions for the LLM to understand available capabilities
FUNCTION_DESCRIPTIONS = {
    "search_web": "Search the web for current information, news, or facts. Use this when the user asks about recent events, needs up-to-date information, or when you need to verify facts. Parameters: query (required), max_results (optional, default: 3)",
    "get_latest_news": "Get the latest news on a specific topic. Use this when the user asks for recent news or current events. Parameters: topic (optional, default: 'technology'), max_results (optional, default: 5)",
    "get_weather": "Get current weather information for a specific location. Use this when the user asks about weather conditions. Parameters: location (required)"
}

# Function implementations
def execute_function_call(function_name: str, parameters: Dict[str, Any]) -> str:
    """Execute a function call and return the result as a string"""
    try:
        if function_name == "search_web":
            query = parameters.get("query", "")
            max_results = parameters.get("max_results", 3)
            results = perform_web_search(query, max_results)
            if results:
                return format_search_results(results)
            else:
                return "I couldn't find any information about that topic. Please try a different search query."
        
        elif function_name == "get_latest_news":
            topic = parameters.get("topic", "technology")
            max_results = parameters.get("max_results", 5)
            results = get_news(topic, max_results)
            if results:
                return format_news_results(results, topic)
            else:
                return f"I couldn't find any recent news about {topic}. The news service might be unavailable."
        
        elif function_name == "get_weather":
            location = parameters.get("location", "")
            results = get_weather(location)
            if results:
                return format_weather_results(results, location)
            else:
                return f"I couldn't get weather information for {location}. Please check the location name and try again."
        
        else:
            return f"Unknown function: {function_name}"
    
    except Exception as e:
        logger.error(f"Function execution error: {e}")
        return f"Error executing function: {str(e)}"

def format_search_results(results: List[Dict]) -> str:
    """Format search results into a readable string"""
    if not results:
        return "No results found."
    
    formatted = "Here's what I found:\n\n"
    for i, result in enumerate(results, 1):
        formatted += f"{i}. {result.get('title', 'No title')}\n"
        formatted += f"   {result.get('content', 'No content')[:200]}...\n"
        formatted += f"   Source: {result.get('url', 'No URL')}\n\n"
    
    return formatted

def format_news_results(results: List[Dict], topic: str) -> str:
    """Format news results into a readable string"""
    if not results:
        return f"No recent news found about {topic}."
    
    formatted = f"Here are the latest news about {topic}:\n\n"
    for i, result in enumerate(results, 1):
        formatted += f"{i}. {result.get('title', 'No title')}\n"
        formatted += f"   {result.get('content', 'No content')[:150]}...\n\n"
    
    return formatted

def format_weather_results(results: List[Dict], location: str) -> str:
    """Format weather results into a readable string"""
    if not results:
        return f"No weather information found for {location}."
    
    # For weather, we typically expect one result with detailed info
    result = results[0]
    return f"Weather information for {location}:\n\n{result.get('content', 'No weather details available')}"

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

def format_search_results(results: List[Dict]) -> str:
    """Format search results into a readable string"""
    if not results:
        return "No results found."
    
    formatted = "Here's what I found:\n\n"
    for i, result in enumerate(results, 1):
        formatted += f"{i}. {result.get('title', 'No title')}\n"
        formatted += f"   {result.get('content', 'No content')[:200]}...\n"
        formatted += f"   Source: {result.get('url', 'No URL')}\n\n"
    
    return formatted

def format_news_results(results: List[Dict], topic: str) -> str:
    """Format news results into a readable string"""
    if not results:
        return f"No recent news found about {topic}."
    
    formatted = f"Here are the latest news about {topic}:\n\n"
    for i, result in enumerate(results, 1):
        formatted += f"{i}. {result.get('title', 'No title')}\n"
        formatted += f"   {result.get('content', 'No content')[:150]}...\n\n"
    
    return formatted

def format_weather_results(results: List[Dict], location: str) -> str:
    """Format weather results into a readable string"""
    if not results:
        return f"No weather information found for {location}."
    
    # For weather, we typically expect one result with detailed info
    result = results[0]
    return f"Weather information for {location}:\n\n{result.get('content', 'No weather details available')}"

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
