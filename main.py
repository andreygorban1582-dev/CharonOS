import asyncio
import os
import threading

from assistant.speech import listen, speak
from assistant.brain import get_response
from assistant.telegram_bot import run_bot, send_notification
from assistant.utils import is_urgent

LISTEN_TIMEOUT = int(os.getenv("LISTEN_TIMEOUT", "10"))


def telegram_thread():
    """Run the Telegram bot in a background thread."""
    run_bot()


async def voice_loop():
    """Main loop for voice interaction."""
    conversation_history = []
    while True:
        user_input = listen(timeout=LISTEN_TIMEOUT)
        if user_input:
            speak("Let me think...")
            reply, conversation_history = get_response(user_input, conversation_history)
            speak(reply)
            if is_urgent(user_input):
                await send_notification(
                    f"User said: {user_input}\nAssistant replied: {reply}"
                )
        await asyncio.sleep(1)


if __name__ == "__main__":
    # Run Telegram bot in a separate daemon thread
    t = threading.Thread(target=telegram_thread, daemon=True)
    t.start()

    # Run voice loop in the asyncio event loop
    asyncio.run(voice_loop())
