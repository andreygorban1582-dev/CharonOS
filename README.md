# AI Assistant with Voice & Telegram

This project implements a personal AI assistant that:
- Listens to voice commands (microphone) and speaks back.
- Responds via Telegram when you message the bot.
- Uses OpenRouter API (free models) for AI conversations.
- Runs on Raspberry Pi, Windows, or GitHub Codespaces.

## Setup

1. Clone this repository.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your Telegram bot token, OpenRouter API key, and user ID
   ```
4. For microphone support on Linux/Raspberry Pi, you may need to install portaudio and espeak:
   ```bash
   sudo apt-get install portaudio19-dev python3-pyaudio espeak
   ```
5. Run the assistant:
   ```bash
   python main.py
   ```

## Usage

- **Voice**: Speak to the microphone; the assistant will reply aloud.
- **Telegram**: Message your bot to chat remotely.

## Customization

- Change the AI model in `assistant/brain.py` (see [OpenRouter models](https://openrouter.ai/models)).
- Switch TTS between offline (`pyttsx3`) and online (`gTTS`) by setting `TTS_MODE=online` in `.env`.
- Add wake word detection (see `wake_word/` folder for optional integration).

## Notes

- Keep your `.env` file private — it is listed in `.gitignore` and should never be committed.
- The free OpenRouter model may have rate limits; consider upgrading for heavy use.
