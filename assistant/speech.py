import os
import tempfile

import speech_recognition as sr
import pyttsx3
from gtts import gTTS
import playsound

# Choose TTS mode: offline (pyttsx3) or online (gTTS). Set via env or default offline.
TTS_MODE = os.getenv("TTS_MODE", "offline")


def listen(timeout=5, phrase_time_limit=5):
    """Capture microphone input and return transcribed text."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
    try:
        text = r.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        return ""


def speak(text):
    """Convert text to speech and play it."""
    if TTS_MODE == "offline":
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    else:
        tts = gTTS(text=text, lang="en")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tmp_path = fp.name
        try:
            tts.save(tmp_path)
            playsound.playsound(tmp_path)
        finally:
            os.remove(tmp_path)
