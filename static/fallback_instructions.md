# How to Create fallback.mp3

## Method 1: Using Online TTS Services
1. Go to a free text-to-speech website like:
   - https://ttsmp3.com/
   - https://www.naturalreaders.com/online/
   - https://www.text2speech.org/

2. Enter the text: "I'm having trouble connecting right now."

3. Download the generated MP3 file

4. Save it as `fallback.mp3` in the static folder

## Method 2: Using Python (if you have gTTS installed)
```bash
pip install gtts
```

```python
from gtts import gTTS

tts = gTTS("I'm having trouble connecting right now.")
tts.save("static/fallback.mp3")
```

## Method 3: Record Your Voice
1. Use any audio recording software
2. Record the phrase "I'm having trouble connecting right now."
3. Export as MP3 format
4. Save to static/fallback.mp3

## Method 4: Use Existing Audio
You can use any short audio file that contains a similar message.

Once you have created the fallback.mp3 file, the application should work properly with the fallback mechanism.
