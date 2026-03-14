import threading
from gui.app import run_gui
from assistant.telegram_bot import run_bot


def start_telegram():
    run_bot()


if __name__ == "__main__":
    # Start Telegram bot in a daemon thread
    t = threading.Thread(target=start_telegram, daemon=True)
    t.start()

    # Run GUI (blocks until window is closed)
    run_gui()
