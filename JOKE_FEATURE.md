# Joke Feature Documentation

## Overview
The AI Voice Agent now includes a joke feature that allows users to request random jokes with audio responses.

## API Endpoint

### GET /joke
Returns a random joke with an audio response.

**Response Format:**
```json
{
  "audio_url": "https://murf.ai/audio/example.mp3",
  "text": "Why don't scientists trust atoms? Because they make up everything!",
  "error": null
}
```

**Response Model:** `SpeechResponse`

## How to Use

### 1. Direct API Call
```bash
curl -X GET "http://localhost:8000/joke"
```

### 2. Web Interface
Visit the main page and use voice commands like:
- "Tell me a joke"
- "I want to hear a joke"
- "Make me laugh"

### 3. Programmatic Usage
```python
import requests

response = requests.get("http://localhost:8000/joke")
if response.status_code == 200:
    joke_data = response.json()
    print(f"Joke: {joke_data.get('text')}")
    print(f"Audio: {joke_data.get('audio_url')}")
```

## Joke Collection
The system currently includes 5 pre-defined jokes:
1. Science joke about atoms
2. Scarecrow award joke
3. Programmer nature joke
4. Spaghetti pun
5. Math book joke

## Error Handling
- If Murf TTS fails, falls back to system TTS
- If both TTS systems fail, returns fallback WAV file
- Proper error messages are included in the response

## Testing
Run the test script to verify functionality:
```bash
python test_joke_endpoint.py
```

## Integration
The joke feature integrates seamlessly with:
- Existing audio generation pipeline
- Error handling system
- Session management
- WebSocket streaming (when triggered via voice)
