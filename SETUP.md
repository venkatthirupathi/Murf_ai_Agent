# Setup Guide for AI Voice Agent

## Environment Variables

Create a `.env` file in the project root with the following variables:

# Murf AI Voice Agent - Environment Variables
MURF_API_KEY=ap2_7da475a6-3c2d-4219-83ae-9b675bbe26ef
ASSEMBLYAI_API_KEY=b410a736cee549099f291d618ae2a4cd
GEMINI_API_KEY=AIzaSyBbpR1aXfO2SAecOrIuztyUflKfyQldYQQ


# Optional: Set to "development" for debug logging
ENVIRONMENT=development
```

## Getting API Keys

1. **Murf AI**: Sign up at [murf.ai](https://murf.ai) and get your API key
2. **AssemblyAI**: Sign up at [assemblyai.com](https://assemblyai.com) and get your API key
3. **Google Gemini**: Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python -m uvicorn app:app --reload
   ```

3. Open [http://localhost:8000](http://localhost:8000) in your browser

## Troubleshooting

- Make sure all API keys are set in your `.env` file
- Check that the `static/fallback.mp3` file exists (or create a placeholder)
- Ensure your microphone permissions are enabled in the browser
- Check the console logs for any error messages
