import wave

# Create a simple test audio file
with wave.open('test_audio.wav', 'wb') as wf:
    wf.setnchannels(1)  # Mono
    wf.setsampwidth(2)  # 16-bit
    wf.setframerate(16000)  # 16kHz sample rate
    # Generate 1 second of silence
    wf.writeframes(b'\x00\x00' * 16000)

print("Test audio file created: test_audio.wav")
