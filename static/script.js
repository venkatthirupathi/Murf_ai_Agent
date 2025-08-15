document.addEventListener('DOMContentLoaded', () => {
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

    let isRecording = false;
    let mediaRecorder;
    let audioChunks = [];

    const recordBtn = document.getElementById('record-btn');
    const recordText = document.getElementById('record-text');
    const echoAudio = document.getElementById('echo-audio');
    const statusText = document.getElementById('status-text');

    // Auto-start recording after AI finishes reply
    echoAudio.onended = () => {
        startRecording();
    };

    // Handle audio playback errors
    echoAudio.onerror = () => {
        console.error('Audio playback error');
        statusText.style.color = '#E74C3C';
        statusText.innerText = "Audio playback failed. Please try again.";
        startRecording();
    };

    recordBtn.addEventListener('click', () => {
        if (isRecording) stopRecording();
        else startRecording();
    });

    async function startRecording() {
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
                sendToBackend();
            };

            mediaRecorder.start();
            isRecording = true;
            recordText.textContent = "Stop Recording";
            recordBtn.classList.add("recording");
            statusText.style.color = '#3498db';
            statusText.innerText = "Listening...";
        } catch (err) {
            console.error('Microphone access error:', err);
            statusText.style.color = '#E74C3C';
            statusText.innerText = "Microphone access denied or unavailable.";
            alert("Microphone access denied or unavailable. Please enable microphone permissions and refresh the page.");
        }
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            // Stop all tracks to release microphone
            if (mediaRecorder.stream) {
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
            }
        }
        isRecording = false;
        recordText.textContent = "Start Recording";
        recordBtn.classList.remove("recording");
        statusText.style.color = '#f39c12';
        statusText.innerText = "Processing your voice...";
    }

    function sendToBackend() {
        if (audioChunks.length === 0) {
            statusText.style.color = '#E74C3C';
            statusText.innerText = "No audio recorded. Please try again.";
            console.error("No audio chunks recorded");
            return;
        }

        console.log(`Sending ${audioChunks.length} audio chunks to backend...`);
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        console.log(`Audio blob created: ${audioBlob.size} bytes, type: ${audioBlob.type}`);

        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.webm');
        console.log(`FormData created with file: ${audioBlob.size} bytes`);

        fetch(`/agent/chat/${sessionId}`, {
            method: 'POST',
            body: formData
        })
            .then(res => {
                console.log(`Backend response status: ${res.status} ${res.statusText}`);
                if (!res.ok) {
                    throw new Error(`Server error: ${res.status} ${res.statusText}`);
                }
                return res.json();
            })
            .then(data => {
                console.log('Backend response data:', data);
                if (data.audio_urls && data.audio_urls.length > 0) {
                    // Play the first audio response
                    echoAudio.src = data.audio_urls[0];
                    console.log(`Playing audio from: ${data.audio_urls[0]}`);
                    echoAudio.play().catch(err => {
                        console.error('Audio play error:', err);
                        statusText.style.color = '#E74C3C';
                        statusText.innerText = "Audio playback failed. Please try again.";
                    });

                    if (data.error) {
                        statusText.style.color = '#E67E22';
                        statusText.innerText = "⚠️ Fallback: " + data.llm_response;
                        console.warn('Response contains error:', data.error);
                    } else {
                        statusText.style.color = '#4CAF50';
                        statusText.innerText = "AI responding...";
                        console.log('AI response successful');
                    }

                    // Log conversation for debugging
                    if (data.transcript) {
                        console.log('User said:', data.transcript);
                    }
                    if (data.llm_response) {
                        console.log('AI responded:', data.llm_response);
                    }
                } else {
                    console.error('No audio URLs in response:', data);
                    throw new Error("No audio URLs in response");
                }
            })
            .catch(err => {
                console.error('Backend error:', err);
                statusText.style.color = '#E74C3C';
                statusText.innerText = "Sorry — I'm having trouble connecting right now.";

                // Try to play fallback audio
                try {
                    echoAudio.src = "/static/fallback.mp3";
                    echoAudio.play().catch(() => {
                        console.log('Fallback audio not available');
                    });
                } catch (fallbackErr) {
                    console.error('Fallback audio error:', fallbackErr);
                }
            });
    }

    // Add keyboard shortcut (spacebar) for recording
    document.addEventListener('keydown', (e) => {
        if (e.code === 'Space' && e.target === document.body) {
            e.preventDefault();
            if (isRecording) stopRecording();
            else startRecording();
        }
    });

    // Initialize status
    statusText.style.color = '#bdc3c7';
    statusText.innerText = "Click the microphone to start recording";
});
