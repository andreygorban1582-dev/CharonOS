import speech_recognition as sr
import pyttsx3
import os

TTS_MODE = os.getenv("TTS_MODE", "offline")


def listen(timeout=5, phrase_time_limit=5):
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
    if TTS_MODE == "offline":
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    else:
        from gtts import gTTS
        import pygame
        import tempfile

        tts = gTTS(text=text, lang='en')
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            tmp_path = fp.name
            tts.save(tmp_path)

        try:
            pygame.mixer.init()
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
        finally:
            pygame.mixer.music.unload()
            os.remove(tmp_path)
