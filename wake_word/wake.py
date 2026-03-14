"""
Optional wake word detection using Porcupine (pvporcupine).

To use this module:
1. Install the dependency:
       pip install pvporcupine
2. Obtain a free AccessKey from https://picovoice.ai/
3. Set PORCUPINE_ACCESS_KEY in your .env file.
4. Replace the keyword path below with your downloaded .ppn file.

Example usage:
    from wake_word.wake import wait_for_wake_word
    wait_for_wake_word()
"""

import os
import struct

try:
    import pvporcupine
    import pyaudio
    _PORCUPINE_AVAILABLE = True
except ImportError:
    _PORCUPINE_AVAILABLE = False

from dotenv import load_dotenv

load_dotenv()

ACCESS_KEY = os.getenv("PORCUPINE_ACCESS_KEY", "")
KEYWORD = "hey google"  # Built-in keyword; change to your preferred word.


def wait_for_wake_word():
    """Block until the configured wake word is detected."""
    if not _PORCUPINE_AVAILABLE:
        print("pvporcupine is not installed. Skipping wake word detection.")
        return

    porcupine = pvporcupine.create(access_key=ACCESS_KEY, keywords=[KEYWORD])
    pa = pyaudio.PyAudio()
    stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length,
    )

    print(f"Waiting for wake word: '{KEYWORD}'...")
    try:
        while True:
            pcm = stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            result = porcupine.process(pcm)
            if result >= 0:
                print("Wake word detected!")
                break
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        porcupine.delete()
