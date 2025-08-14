# 🎤 AI Voice Agent – 30 Days of Voice Agents Challenge

A full-stack conversational AI voice agent built as part of the #30DaysofVoiceAgents challenge with Murf AI! This project combines speech-to-text, powerful LLM conversation, and realistic voice synthesis, wrapped in a modern, voice-centric UI.

---

## 🚀 Features

-  **Voice-first conversation UI** (single record button with animated states)
-  **Conversation memory**: Multi-turn dialogue, remembers context per session
-  **Speech-to-text**: Uses AssemblyAI for accurate voice transcription
-  **AI responses**: Google Gemini LLM generates context-aware replies
-  **Text-to-speech**: Murf AI delivers human-like audio responses
-  **Automatic error handling** with fallback spoken messages
-  **Modern design:** Clean, focused, and accessible UI

---
## 📸 Screenshots



Task day 12 completed UI:
<img src="task_day_12.png" width="350">


---

## 🔧 Tech Stack

- **Frontend:** HTML5, CSS3, vanilla JavaScript
- **Backend:** FastAPI (Python)
- **APIs/AI Services:** AssemblyAI (STT), Google Gemini LLM, Murf AI (TTS)
- **Others:** dotenv for environment variables, Uvicorn as ASGI server

---




## ⚙️ Getting Started

### 1. **Clone the repository**
       git clone  https://github.com/venkatthirupathi/Murf_ai_project.git


### 2. **Install dependencies**
       pip install -r requirements.txt   (or)  pip install fastapi uvicorn requests python-dotenv python-multipart assemblyai google-generativeai


 
### 3. **Set environment variables**
Create a file called `.env` in the project root and add:


MURF_API_KEY=your-murf-api-key
ASSEMBLYAI_API_KEY=your-assemblyai-api-key
GEMINI_API_KEY=your-gemini-api-key



> **Note:** All 3 keys are required for full functionality. Get them from the respective providers.

### 4. **Run the server**

python -m uvicorn app:app --reload


Then open [http://localhost:8000](http://localhost:8000) in your browser.


## ✨ Credits

- Built as part of the #30DaysofVoiceAgents by  THIRUPATHI VENKAT
- Thanks to [Murf AI](https://murf.ai), [AssemblyAI](https://assemblyai.com), and [Google Gemini](https://deepmind.google/technologies/gemini/) for their APIs and inspiration

#BuildwithMurf #30DaysofVoiceAgents #AI #VoiceBot #FastAPI #MurfAI
