# 🎤 AI Voice Agent – 30 Days of Voice Agents Challenge

A full-stack conversational AI voice agent built as part of the #30DaysofVoiceAgents challenge with Murf AI! This project combines speech-to-text, powerful LLM conversation, and realistic voice synthesis, wrapped in a modern, voice-centric UI with **real-time streaming capabilities**.

---

## 🚀 Features

-  **🎯 Real-time Streaming Responses** - AI responses appear word-by-word as they're generated
-  **🔌 WebSocket Support** - Real-time bidirectional communication with automatic fallback
-  **💬 Conversation Memory** - Multi-turn dialogue with persistent chat history per session
-  **🎤 Voice-first conversation UI** - Single record button with animated states and streaming indicators
-  **🗣️ Speech-to-text** - Uses AssemblyAI for accurate voice transcription
-  **🧠 AI responses** - Google Gemini LLM generates context-aware replies with streaming
-  **🔊 Text-to-speech** - Murf AI delivers human-like audio responses
-  **⚡ Automatic error handling** with fallback spoken messages
-  **🎨 Modern design** - Clean, focused, accessible UI with gradient backgrounds
-  **⌨️ Keyboard shortcuts** - Use spacebar to start/stop recording
-  **📱 Responsive design** - Works perfectly on desktop and mobile devices

---

## 📸 Screenshots

Task day 12 completed UI:
<img src="task_day_12.png" width="350">

**NEW: Today's Streaming Task** - Real-time AI responses with WebSocket support!

---

## 🔧 Tech Stack

- **Frontend:** HTML5, CSS3, vanilla JavaScript with WebSocket support
- **Backend:** FastAPI (Python) with streaming endpoints and WebSocket
- **APIs/AI Services:** AssemblyAI (STT), Google Gemini LLM (streaming), Murf AI (TTS)
- **Real-time:** WebSocket for instant communication, HTTP streaming fallback
- **Others:** dotenv for environment variables, Uvicorn as ASGI server

---

## ⚙️ Getting Started

### 1. **Clone the repository**
```bash
git clone https://github.com/venkatthirupathi/Murf_ai.git
cd Murf_ai
```

### 2. **Install dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Set environment variables**
Create a file called `.env` in the project root and add:

```bash
MURF_API_KEY=your-murf-api-key
ASSEMBLYAI_API_KEY=your-assemblyai-api-key
GEMINI_API_KEY=your-gemini-api-key
```

> **Note:** All 3 keys are required for full functionality. Get them from the respective providers.

### 4. **Create fallback audio**
Create a `static/fallback.mp3` file with a simple message like "I'm having trouble connecting right now"

### 5. **Run the server**

**Option A: Using the startup script (recommended)**
```bash
python run.py
```

**Option B: Using uvicorn directly**
```bash
python -m uvicorn app:app --reload
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

---

## 🔑 Getting API Keys

1. **Murf AI**: Sign up at [murf.ai](https://murf.ai) and get your API key
2. **AssemblyAI**: Sign up at [assemblyai.com](https://assemblyai.com) and get your API key  
3. **Google Gemini**: Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

---

## 🎯 Usage

### **Basic Voice Chat**
1. **Click the microphone button** or press **spacebar** to start recording
2. **Speak your message** clearly into your microphone
3. **Click again or press spacebar** to stop recording
4. **Watch AI respond in real-time** - responses stream word-by-word
5. **Audio plays automatically** when the response is complete
6. **Recording automatically resumes** after the AI finishes speaking

### **Streaming Features**
- **Real-time responses** appear as AI thinks
- **WebSocket connection** for instant communication
- **Automatic fallback** to HTTP streaming if WebSocket fails
- **Persistent chat history** across browser sessions
- **Clear conversation** button to start fresh

---

## 🛠️ Troubleshooting

- **Microphone not working**: Check browser permissions and refresh the page
- **API errors**: Verify all API keys are set correctly in your `.env` file
- **Audio not playing**: Check browser console for errors, ensure fallback.mp3 exists
- **Streaming not working**: Check WebSocket connection status, verify Gemini API supports streaming
- **Connection issues**: Ensure all services are accessible from your network

---

## 📁 Project Structure

```
Murf_ai/
├── app.py              # Main FastAPI application with streaming endpoints
├── run.py              # Startup script
├── requirements.txt    # Python dependencies (updated for streaming)
├── schemas/           # Pydantic data models (includes streaming)
├── services/          # API service integrations (LLM with streaming)
├── static/            # Frontend assets (CSS, JS with WebSocket support)
├── templates/         # HTML templates (enhanced UI)
├── STREAMING_SETUP.md # Detailed streaming setup guide
└── SETUP.md           # Original setup instructions
```

---

## 🆕 What's New Today

### **Streaming Task Implementation**
- ✅ **Real-time AI responses** - See responses as they're generated
- ✅ **WebSocket endpoints** - Instant bidirectional communication
- ✅ **HTTP streaming fallback** - Reliable fallback when WebSocket fails
- ✅ **Enhanced conversation UI** - Modern design with chat history
- ✅ **Persistent sessions** - Chat history saved per session
- ✅ **Better error handling** - Graceful fallbacks for all scenarios

### **Previous Days Features Preserved**
- ✅ **Voice-first interface** - Single button recording
- ✅ **Speech-to-text** - AssemblyAI integration
- ✅ **LLM responses** - Google Gemini integration
- ✅ **Text-to-speech** - Murf AI integration
- ✅ **Error handling** - Fallback mechanisms
- ✅ **Keyboard shortcuts** - Spacebar recording control

---

## ✨ Credits

- Built as part of the #30DaysofVoiceAgents by THIRUPATHI VENKAT
- **Today's Task**: Real-time streaming AI conversations with WebSocket support
- Thanks to [Murf AI](https://murf.ai), [AssemblyAI](https://assemblyai.com), and [Google Gemini](https://deepmind.google/technologies/gemini/) for their APIs and inspiration

#BuildwithMurf #30DaysofVoiceAgents #AI #VoiceBot #FastAPI #MurfAI #Streaming #WebSocket
