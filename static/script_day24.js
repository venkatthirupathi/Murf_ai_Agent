document.addEventListener('DOMContentLoaded', () => {
    const recordBtn = document.getElementById('record-btn');
    const clearBtn = document.getElementById('clear-btn');
    const setPersonaBtn = document.getElementById('set-persona-btn');
    const personaSelect = document.getElementById('persona-select');
    const statusText = document.getElementById('status-text');
    const chatHistory = document.getElementById('chat-history');
    const echoAudio = document.getElementById('echo-audio');

    let mediaRecorder;
    let audioChunks = [];
    let sessionId = localStorage.getItem('sessionId') || `session_${Date.now()}`;
    localStorage.setItem('sessionId', sessionId);

    console.log(`Session ID: ${sessionId}`);

    function addMessageToHistory(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${isUser ? 'user' : 'ai'}`;
        messageDiv.textContent = message;
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function playAudio(url) {
        echoAudio.src = url;
        echoAudio.play().catch(e => console.error('Audio playback failed:', e));
    }

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.ondataavailable = event => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                await sendAudioToServer(audioBlob);
            };

            mediaRecorder.start();
            recordBtn.textContent = '⏹️ Stop Recording';
            statusText.textContent = '🎤 Recording... Speak now!';
        } catch (error) {
            console.error('Error starting recording:', error);
            statusText.textContent = '❌ Could not start recording. Please allow microphone access.';
        }
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            recordBtn.textContent = '🎤 Start Recording';
            statusText.textContent = '⏳ Processing your voice...';
        }
    }

    async function sendAudioToServer(audioBlob) {
        const formData = new FormData();
        formData.append('file', audioBlob, 'audio.wav');

        try {
            statusText.textContent = '🤖 AI is thinking...';
            const response = await fetch(`/agent/chat/${sessionId}`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Add user transcript to history
            if (data.transcript) {
                addMessageToHistory(`You: ${data.transcript}`, true);
            }

            // Add AI response to history
            if (data.llm_response) {
                addMessageToHistory(`AI: ${data.llm_response}`, false);
            }

            // Play audio response
            if (data.audio_urls && data.audio_urls.length > 0) {
                playAudio(data.audio_urls[0]);
            }

            statusText.textContent = '✅ Ready for next message!';

        } catch (error) {
            console.error('Error sending audio:', error);
            statusText.textContent = '❌ Error processing your voice. Please try again.';
            addMessageToHistory('Error: Could not process your voice. Please try again.', false);
        }
    }

    recordBtn.addEventListener('click', () => {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            stopRecording();
        } else {
            startRecording();
        }
    });

    clearBtn.addEventListener('click', () => {
        chatHistory.innerHTML = '<div class="welcome-message"><p>👋 Welcome! Click the microphone to start talking with the AI.</p></div>';
        statusText.textContent = 'Ready to chat!';
    });

    setPersonaBtn.addEventListener('click', async () => {
        const selectedPersona = personaSelect.value;
        try {
            const response = await fetch(`/persona/${sessionId}/${selectedPersona}`, { method: 'POST' });
            const data = await response.json();
            statusText.textContent = `✅ ${data.message}`;
            addMessageToHistory(`System: Persona changed to ${selectedPersona}`, false);
        } catch (error) {
            console.error('Error setting persona:', error);
            statusText.textContent = '❌ Failed to set persona.';
        }
    });

    async function getCurrentPersona() {
        try {
            const response = await fetch(`/persona/${sessionId}`);
            const data = await response.json();
            if (data.persona) {
                personaSelect.value = data.persona;
            }
        } catch (error) {
            console.error('Error getting current persona:', error);
        }
    }

    // Initialize
    getCurrentPersona();
    statusText.textContent = '🎤 Ready to chat! Click the microphone to start.';
});
