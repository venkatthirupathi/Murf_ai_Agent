# Debugging Guide for AI Voice Agent

## Issue: Speech Input Not Producing Output

If you're experiencing issues where speech input isn't producing any output, follow these debugging steps:

## 🔍 Step 1: Check Browser Console

1. Open your browser's Developer Tools (F12)
2. Go to the Console tab
3. Try recording audio and look for error messages
4. Check for any JavaScript errors or network failures

## 🔍 Step 2: Check Server Logs

1. Look at your terminal where the server is running
2. Check for error messages when you submit audio
3. Look for transcription errors or API failures

## 🔍 Step 3: Test API Configuration

Visit these endpoints to check your setup:

- **Health Check**: http://localhost:8000/health
- **Configuration Test**: http://localhost:8000/test-transcription

## 🔍 Step 4: Common Issues and Solutions

### Issue 1: "Empty transcription result"
**Symptoms**: Server logs show "Empty transcription result" error
**Causes**:
- AssemblyAI API key is invalid or missing
- Audio file format not supported
- Audio file is corrupted or empty
- Network issues with AssemblyAI

**Solutions**:
1. Verify your `.env` file has `ASSEMBLYAI_API_KEY=your_key_here`
2. Check if AssemblyAI service is accessible
3. Ensure audio is being recorded properly (check browser console)

### Issue 2: "No audio URLs in response"
**Symptoms**: Frontend shows "No audio URLs in response" error
**Causes**:
- Murf TTS API key is invalid or missing
- TTS service failed to generate audio
- Network issues with Murf API

**Solutions**:
1. Verify your `.env` file has `MURF_API_KEY=your_key_here`
2. Check if Murf service is accessible
3. Check server logs for TTS errors

### Issue 3: "LLM API error"
**Symptoms**: Server logs show "LLM API error"
**Causes**:
- Google Gemini API key is invalid or missing
- Gemini service is down
- Network issues with Google API

**Solutions**:
1. Verify your `.env` file has `GEMINI_API_KEY=your_key_here`
2. Check if Gemini service is accessible
3. Verify your API key has proper permissions

## 🔍 Step 5: Audio Recording Issues

### Check Microphone Permissions
1. Ensure your browser has microphone access
2. Check browser settings for microphone permissions
3. Try refreshing the page after granting permissions

### Check Audio Format
1. The app expects `audio/webm` format
2. Ensure your browser supports WebM recording
3. Check if audio chunks are being created (see console logs)

## 🔍 Step 6: Network Issues

### Check API Endpoints
1. **AssemblyAI**: https://api.assemblyai.com
2. **Murf AI**: https://api.murf.ai
3. **Google Gemini**: https://generativelanguage.googleapis.com

### Test Connectivity
```bash
# Test if you can reach the APIs
curl -I https://api.assemblyai.com
curl -I https://api.murf.ai
curl -I https://generativelanguage.googleapis.com
```

## 🔍 Step 7: Environment Variables

Ensure your `.env` file contains:
```bash
MURF_API_KEY=your_actual_murf_api_key
ASSEMBLYAI_API_KEY=your_actual_assemblyai_api_key
GEMINI_API_KEY=your_actual_gemini_api_key
```

## 🔍 Step 8: Dependencies

Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

## 🔍 Step 9: Restart Server

After making changes:
1. Stop the server (Ctrl+C)
2. Restart: `python run.py`
3. Check for any startup errors

## 🔍 Step 10: Test with Simple Audio

1. Record a simple, clear phrase like "Hello, how are you?"
2. Speak slowly and clearly
3. Ensure there's minimal background noise
4. Check if the audio file size is reasonable (> 1KB)

## 📋 Debugging Checklist

- [ ] Browser console shows no JavaScript errors
- [ ] Server logs show successful audio file reception
- [ ] Transcription service returns text (not empty)
- [ ] LLM service generates response
- [ ] TTS service generates audio URLs
- [ ] Frontend receives and plays audio

## 🆘 Still Having Issues?

If you're still experiencing problems:

1. Check the server logs for specific error messages
2. Verify all API keys are valid and active
3. Test each service individually
4. Check your network/firewall settings
5. Ensure you have sufficient API credits/quota

## 📞 Support

For additional help:
- Check the main README.md for setup instructions
- Review the SETUP.md file for configuration details
- Check the console logs and server logs for specific error messages
