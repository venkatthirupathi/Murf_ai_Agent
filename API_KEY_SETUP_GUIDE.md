# API Key Setup Guide for Murf AI Conversational Agent

## 1. Murf AI API Key
### Steps to get Murf AI API Key:
1. Go to https://murf.ai
2. Sign up for an account
3. Navigate to the API section in your dashboard
4. Generate a new API key
5. Copy the API key

### Usage:
- Used for text-to-speech conversion
- Required for high-quality voice generation
- Fallback TTS available but limited

## 2. AssemblyAI API Key
### Steps to get AssemblyAI API Key:
1. Go to https://assemblyai.com
2. Sign up for a free account
3. Go to your dashboard
4. Copy your API key from the account settings
5. Free tier includes 5 hours of transcription per month

### Usage:
- Used for speech-to-text transcription
- Real-time audio processing
- Essential for voice input functionality

## 3. Google Gemini API Key
### Steps to get Google Gemini API Key:
1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Create a new API key
4. Copy the generated key
5. Free tier available with usage limits

### Usage:
- Powers the conversational AI responses
- Handles natural language understanding
- Generates contextual responses

## Configuration Steps:

1. **Edit the `.env` file** and replace the placeholder values:
```bash
MURF_API_KEY=your_actual_murf_api_key_here
ASSEMBLYAI_API_KEY=your_actual_assemblyai_api_key_here  
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

2. **Save the file** and run the configuration check:
```bash
python check_config.py
```

3. **Run integration tests** to verify everything works:
```bash
python test_core_integration.py
```

4. **Start the application**:
```bash
uvicorn app:app --reload
```

5. **Access the web interface** at http://localhost:8000

## Troubleshooting:

- If you get API key errors, double-check that you've copied the keys correctly
- Ensure there are no extra spaces in the `.env` file
- Check that the API services are accessible from your location
- The application includes fallback mechanisms for testing without all APIs

## Note:
All three services offer free tiers that should be sufficient for development and testing. For production use, you may need to upgrade to paid plans based on your usage requirements.
