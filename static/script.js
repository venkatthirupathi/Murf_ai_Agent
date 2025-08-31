document.addEventListener('DOMContentLoaded', () => {
    const recordBtn = document.getElementById('record-btn');
    const clearBtn = document.getElementById('clear-btn');
    const checkFilesBtn = document.getElementById('check-files-btn');
    const setPersonaBtn = document.getElementById('set-persona-btn');
    const personaSelect = document.getElementById('persona-select');
    const statusText = document.getElementById('status-text');
    const chatHistory = document.getElementById('chat-history');
    const streamingResponse = document.getElementById('streaming-response');
    const responseText = document.getElementById('response-text');
    const echoAudio = document.getElementById('echo-audio');
    const wsStatus = document.getElementById('ws-status');

    let websocket;
    let mediaRecorder;
    let audioChunks = [];
    let sessionId = localStorage.getItem('sessionId') || `session_${Date.now()}`;
    localStorage.setItem('sessionId', sessionId);

    console.log(`Session ID: ${sessionId}`);

    function initializeWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;
        console.log(`WebSocket URL: ${wsUrl}`);

        try {
            websocket = new WebSocket(wsUrl);

            websocket.onopen = () => {
                console.log('WebSocket connected');
                wsStatus.textContent = '🟢 WebSocket: Connected - Ready for Audio Streaming';
                wsStatus.className = 'ws-status connected';
            };

            websocket.onmessage = handleWebSocketMessage;

            websocket.onclose = () => {
                console.log('WebSocket disconnected');
                wsStatus.textContent = '🔴 WebSocket: Disconnected';
                wsStatus.className = 'ws-status';
                setTimeout(initializeWebSocket, 5000); // Try to reconnect
            };

            websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                wsStatus.textContent = '🔴 WebSocket: Error';
                wsStatus.className = 'ws-status';
            };
        } catch (error) {
            console.error('Failed to initialize WebSocket:', error);
            wsStatus.textContent = '🔴 WebSocket: Failed to connect';
        }
    }

    function handleWebSocketMessage(event) {
        const message = JSON.parse(event.data);
        console.log('Received message:', message);

        switch (message.type) {
            case 'ready':
                statusText.textContent = 'Ready to stream audio.';
                break;
            case 'transcript':
                updateTranscript(message.content, message.final);
                break;
            case 'turn_end':
                streamingResponse.style.display = 'block';
                responseText.textContent = '';
                break;
            case 'llm_chunk':
                responseText.textContent += message.content;
                break;
            case 'audio_ready':
                streamingResponse.style.display = 'none';
                playAudio(message.audio_url);
                break;
            case 'complete':
                streamingResponse.style.display = 'none';
                break;
            case 'error':
                statusText.textContent = `Error: ${message.message}`;
                streamingResponse.style.display = 'none';
                break;
            default:
                console.warn('Unknown message type:', message.type);
        }
    }

    function updateTranscript(transcript, isFinal) {
        let transcriptContainer = document.getElementById('transcript-container');
        if (!transcriptContainer) {
            transcriptContainer = document.createElement('div');
            transcriptContainer.id = 'transcript-container';
            transcriptContainer.className = 'chat-message user';
            chatHistory.appendChild(transcriptContainer);
        }
        transcriptContainer.textContent = transcript;
        if (isFinal) {
            transcriptContainer.id = ''; // Reset id
        }
    }

    function playAudio(url) {
        echoAudio.src = url;
        echoAudio.play().catch(e => console.error('Audio playback failed:', e));
    }

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = event => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                    if (websocket && websocket.readyState === WebSocket.OPEN) {
                        websocket.send(event.data);
                    }
                }
            };
            mediaRecorder.onstop = () => {
                // The audio is sent in chunks, no need to send a blob at the end
            };
            audioChunks = [];
            mediaRecorder.start(500); // Send data every 500ms to stay within AssemblyAI limits
            recordBtn.textContent = 'Stop Recording';
            statusText.textContent = 'Recording...';
        } catch (error) {
            console.error('Error starting recording:', error);
            statusText.textContent = 'Could not start recording. Please allow microphone access.';
        }
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
            recordBtn.textContent = 'Start Recording';
            statusText.textContent = 'Recording stopped.';
        }
    }

    recordBtn.addEventListener('click', () => {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            stopRecording();
        } else {
            startRecording();
        }
    });

    clearBtn.addEventListener('click', async () => {
        try {
            await fetch(`/conversation/${sessionId}`, { method: 'DELETE' });
            chatHistory.innerHTML = '<div class="welcome-message"><p>Conversation cleared.</p></div>';
            statusText.textContent = 'Conversation cleared.';
        } catch (error) {
            console.error('Error clearing conversation:', error);
            statusText.textContent = 'Failed to clear conversation.';
        }
    });

    checkFilesBtn.addEventListener('click', async () => {
        try {
            const response = await fetch(`/recorded-audio/${sessionId}`);
            const data = await response.json();
            let fileList = 'No files found.';
            if (data.files && data.files.length > 0) {
                fileList = data.files.map(f => `${f.filename} (${f.size_mb} MB)`).join('\n');
            }
            alert(`Recorded files for session ${sessionId}:\n${fileList}`);
        } catch (error) {
            console.error('Error checking files:', error);
            alert('Failed to check files.');
        }
    });

    setPersonaBtn.addEventListener('click', async () => {
        const selectedPersona = personaSelect.value;
        try {
            const response = await fetch(`/persona/${sessionId}/${selectedPersona}`, { method: 'POST' });
            const data = await response.json();
            statusText.textContent = data.message;
        } catch (error) {
            console.error('Error setting persona:', error);
            statusText.textContent = 'Failed to set persona.';
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

    // Initializations
    initializeWebSocket();
    getCurrentPersona();
});