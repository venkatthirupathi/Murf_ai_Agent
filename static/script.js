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

    // Auto‑start recording after AI finishes reply
    echoAudio.onended = () => {
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
            mediaRecorder = new MediaRecorder(stream);

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
            statusText.innerText = "Listening...";
        } catch (err) {
            alert("Microphone access denied or unavailable.");
        }
    }

    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
        }
        isRecording = false;
        recordText.textContent = "Start Recording";
        recordBtn.classList.remove("recording");
        statusText.innerText = "Processing your voice...";
    }

    function sendToBackend() {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('file', audioBlob, 'recording.webm');

        fetch(`/agent/chat/${sessionId}`, { method: 'POST', body: formData })
        .then(res => {
            if (!res.ok) throw new Error("Server error");
            return res.json();
        })
        .then(data => {
            if (data.audio_urls && data.audio_urls.length > 0) {
                echoAudio.src = data.audio_urls[0];
                echoAudio.play();
                if (data.error) {
                    statusText.style.color = '#E67E22';
                    statusText.innerText = "⚠️ Fallback: " + data.llm_response;
                } else {
                    statusText.style.color = '#4CAF50';
                    statusText.innerText = "AI responding...";
                }
            } else {
                throw new Error("No audio URLs in response");
            }
        })
        .catch(err => {
            statusText.style.color = '#E74C3C';
            statusText.innerText = "Sorry — I'm having trouble connecting right now.";
            echoAudio.src = "/static/fallback.mp3";
            echoAudio.play();
        });
    }
});
