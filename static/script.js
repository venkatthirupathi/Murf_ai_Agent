document.addEventListener('DOMContentLoaded', () => {
    // Session management
    function getOrCreateSessionId() {
        const params = new URLSearchParams(window.location.search);
        let sessionId = params.get('session');
        if (!sessionId) {
            sessionId = Date.now().toString();
            params.set('session', sessionId);
            window.history.replaceState({}, '', `${location.pathname}?${params}`);
        }
        return sessionId;
    }

    const sessionId = getOrCreateSessionId();

    // State variables
    let isRecording = false;
    let mediaRecorder;
    let audioChunks = [];
    let websocket = null;
    let isStreaming = false;

    // DOM elements
    const recordBtn = document.getElementById('record-btn');
    const recordText = document.getElementById('record-text');
    const clearBtn = document.getElementById('clear-btn');
    const echoAudio = document.getElementById('echo-audio');
    const statusText = document.getElementById('status-text');
    const chatHistory = document.getElementById('chat-history');
    const streamingResponse = document.getElementById('streaming-response');
    const responseText = document.getElementById('response-text');
    const wsStatus = document.getElementById('ws-status');

    // Initialize
    initializeWebSocket();
    loadConversationHistory();

    // Event listeners
    recordBtn.addEventListener('click', () => {
        if (isRecording) stopRecording();
        else startRecording();
    });

    clearBtn.addEventListener('click', clearConversation);

    // Auto-start recording after AI finishes reply
    echoAudio.onended = () => {
        if (!isStreaming) {
            startRecording();
        }
    };

    // Handle audio playback errors
    echoAudio.onerror = () => {
        console.error('Audio playback error');
        updateStatus("Audio playback failed. Please try again.", 'error');
        if (!isStreaming) {
            startRecording();
        }
    };

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.code === 'Space' && e.target === document.body) {
            e.preventDefault();
            if (isRecording) stopRecording();
            else startRecording();
        }
    });

    // WebSocket initialization
    function initializeWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;
        
        try {
            websocket = new WebSocket(wsUrl);
            
            websocket.onopen = () => {
                console.log('WebSocket connected');
                wsStatus.textContent = '🟢 WebSocket: Connected';
                wsStatus.className = 'ws-status connected';
            };
            
            websocket.onmessage = handleWebSocketMessage;
            
            websocket.onclose = () => {
                console.log('WebSocket disconnected');
                wsStatus.textContent = '🔴 WebSocket: Disconnected';
                wsStatus.className = 'ws-status';
                // Try to reconnect after 5 seconds
                setTimeout(initializeWebSocket, 5000);
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

    // Handle WebSocket messages
    function handleWebSocketMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message:', data);
            
            switch (data.type) {
                case 'transcript':
                    addMessageToHistory('user', data.content);
                    break;
                    
                case 'llm_chunk':
                    if (!isStreaming) {
                        startStreamingResponse();
                    }
                    appendToResponse(data.content);
                    break;
                    
                case 'audio_ready':
                    completeStreamingResponse(data.audio_url);
                    break;
                    
                case 'complete':
                    isStreaming = false;
                    break;
                    
                case 'error':
                    updateStatus(data.message, 'error');
                    if (isStreaming) {
                        isStreaming = false;
                        streamingResponse.style.display = 'none';
                    }
                    break;
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }

    // Recording functions
    async function startRecording() {
        if (isStreaming) return;
        
        audioChunks = [];
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });

            mediaRecorder.ondataavailable = event => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = () => {
                sendAudioToWebSocket();
            };

            mediaRecorder.start();
            isRecording = true;
            recordText.textContent = "Stop Recording";
            recordBtn.classList.add("recording");
            updateStatus("Listening...", 'listening');
        } catch (err) {
            console.error('Microphone access error:', err);
            updateStatus("Microphone access denied or unavailable.", 'error');
            alert("Microphone access denied or unavailable. Please enable microphone permissions and refresh the page.");
        }
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            if (mediaRecorder.stream) {
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
            }
        }
        isRecording = false;
        recordText.textContent = "Start Recording";
        recordBtn.classList.remove("recording");
        updateStatus("Processing your voice...", 'processing');
    }

    // Send audio via WebSocket
    function sendAudioToWebSocket() {
        if (audioChunks.length === 0) {
            updateStatus("No audio recorded. Please try again.", 'error');
            console.error("No audio chunks recorded");
            return;
        }

        if (websocket && websocket.readyState === WebSocket.OPEN) {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            websocket.send(audioBlob);
            console.log(`Audio sent via WebSocket: ${audioBlob.size} bytes`);
        } else {
            // Fallback to HTTP endpoint if WebSocket is not available
            sendAudioViaHTTP();
        }
    }

    // Fallback HTTP method
    function sendAudioViaHTTP() {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.webm');

        fetch(`/agent/chat/${sessionId}/stream`, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.body.getReader();
        })
        .then(reader => {
            return new ReadableStream({
                start(controller) {
                    return pump();
                    function pump() {
                        return reader.read().then(({ done, value }) => {
                            if (done) {
                                controller.close();
                                return;
                            }
                            controller.enqueue(value);
                            return pump();
                        });
                    }
                }
            });
        })
        .then(stream => new Response(stream))
        .then(response => response.text())
        .then(text => {
            const lines = text.trim().split('\n');
            lines.forEach(line => {
                if (line.trim()) {
                    try {
                        const data = JSON.parse(line);
                        handleStreamingResponse(data);
                    } catch (e) {
                        console.error('Error parsing streaming response:', e);
                    }
                }
            });
        })
        .catch(error => {
            console.error('HTTP streaming error:', error);
            updateStatus("Connection error. Please try again.", 'error');
        });
    }

    // Handle streaming responses
    function handleStreamingResponse(data) {
        switch (data.type) {
            case 'llm_chunk':
                if (!isStreaming) {
                    startStreamingResponse();
                }
                appendToResponse(data.content);
                break;
                
            case 'audio_ready':
                completeStreamingResponse(data.audio_url);
                break;
                
            case 'complete':
                isStreaming = false;
                break;
                
            case 'error':
                updateStatus(data.message, 'error');
                if (isStreaming) {
                    isStreaming = false;
                    streamingResponse.style.display = 'none';
                }
                break;
        }
    }

    // Streaming response management
    function startStreamingResponse() {
        isStreaming = true;
        streamingResponse.style.display = 'block';
        responseText.textContent = '';
        updateStatus("AI is responding...", 'responding');
    }

    function appendToResponse(text) {
        responseText.textContent += text;
        // Auto-scroll to bottom
        streamingResponse.scrollTop = streamingResponse.scrollHeight;
    }

    function completeStreamingResponse(audioUrl) {
        if (audioUrl) {
            echoAudio.src = audioUrl;
            echoAudio.play().catch(err => {
                console.error('Audio play error:', err);
                updateStatus("Audio playback failed. Please try again.", 'error');
            });
        }
        
        // Add AI response to chat history
        const aiResponse = responseText.textContent;
        if (aiResponse.trim()) {
            addMessageToHistory('ai', aiResponse);
        }
        
        // Hide streaming response
        setTimeout(() => {
            streamingResponse.style.display = 'none';
            responseText.textContent = '';
        }, 1000);
    }

    // Chat history management
    function addMessageToHistory(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}`;
        
        const roleSpan = document.createElement('div');
        roleSpan.className = 'role';
        roleSpan.textContent = role === 'user' ? 'You' : 'AI Assistant';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(roleSpan);
        messageDiv.appendChild(contentDiv);
        
        // Remove welcome message if it exists
        const welcomeMessage = chatHistory.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
        
        // Save to session storage
        saveConversationToStorage();
    }

    function loadConversationHistory() {
        const saved = sessionStorage.getItem(`conversation_${sessionId}`);
        if (saved) {
            try {
                const history = JSON.parse(saved);
                history.forEach(msg => {
                    addMessageToHistory(msg.role, msg.content);
                });
            } catch (e) {
                console.error('Error loading conversation history:', e);
            }
        }
    }

    function saveConversationToStorage() {
        const messages = Array.from(chatHistory.querySelectorAll('.chat-message')).map(msg => ({
            role: msg.classList.contains('user') ? 'user' : 'ai',
            content: msg.querySelector('.content').textContent
        }));
        sessionStorage.setItem(`conversation_${sessionId}`, JSON.stringify(messages));
    }

    function clearConversation() {
        if (confirm('Are you sure you want to clear the conversation?')) {
            chatHistory.innerHTML = `
                <div class="welcome-message">
                    <p>👋 Welcome! Click the microphone to start talking with your AI assistant.</p>
                    <p>Your conversation will appear here in real-time.</p>
                </div>
            `;
            sessionStorage.removeItem(`conversation_${sessionId}`);
            updateStatus("Conversation cleared. Ready to start fresh!", 'info');
        }
    }

    // Status updates
    function updateStatus(message, type = 'info') {
        statusText.textContent = message;
        statusText.className = 'status-text';
        
        // Add type-specific styling
        switch (type) {
            case 'error':
                statusText.style.color = '#E74C3C';
                break;
            case 'success':
                statusText.style.color = '#27AE60';
                break;
            case 'listening':
                statusText.style.color = '#3498db';
                break;
            case 'processing':
                statusText.style.color = '#f39c12';
                break;
            case 'responding':
                statusText.style.color = '#9c27b0';
                break;
            default:
                statusText.style.color = '#333';
        }
    }

    // Initialize status
    updateStatus("Click the microphone to start recording", 'info');
});
