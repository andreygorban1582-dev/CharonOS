# Rick Assistant

An AI assistant with a **Rick Sanchez** personality — voice input/output, a Windows GUI, Telegram bot, DOOM integration, and an OpenRouter-powered brain.

Runs on Windows, Raspberry Pi, or GitHub Codespaces.

---

## Features

- 🎤 **Voice input** (microphone) and **text-to-speech** output
- 🖥️ **Windows GUI** (Tkinter) with a dark, terminal-style theme
- 📱 **Telegram bot** interface — message Rick from anywhere
- 🧠 **Rick Sanchez AI personality** via OpenRouter (free models)
- 🔥 **Play DOOM** — click a button or ask Rick to launch the game
- 📦 **Legion Go installer** — build a portable `.exe` with PyInstaller

---

## Project Structure

```
rick-assistant/
├── .env.example             # Template for environment variables
├── .gitignore
├── requirements.txt
├── README.md
├── main.py                  # Entry point: launches GUI and Telegram bot threads
├── assistant/
│   ├── __init__.py
│   ├── speech.py            # Speech-to-text & TTS
│   ├── brain.py             # Rick AI via OpenRouter (persona injected)
│   ├── telegram_bot.py      # Telegram bot handlers
│   └── utils.py
├── gui/
│   ├── __init__.py
│   ├── app.py               # Tkinter GUI for Windows
│   └── assets/              # Icons, etc. (optional)
├── doom/
│   ├── launcher.py          # Launches DOOM using external engine
│   └── README.md            # Instructions to get DOOM shareware WAD
└── installer/
    └── build_exe.bat        # PyInstaller build script for Legion Go
```

---

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd rick-assistant
```

### 2. Create your `.env` file

Copy the example and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```
TELEGRAM_BOT_TOKEN=<your Telegram bot token>
OPENROUTER_API_KEY=<your OpenRouter API key>
MY_USER_ID=<your Telegram user ID>
TTS_MODE=offline
```

> ⚠️ **Never commit `.env` to version control.** It is already listed in `.gitignore`.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Windows / PyAudio note:** If `pip install pyaudio` fails, download the matching wheel from
> [https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
> and install it with `pip install <wheel_file>.whl`.

### 4. (Optional) Set up DOOM

Follow the instructions in [doom/README.md](doom/README.md).

### 5. Run

```bash
python main.py
```

This starts the Tkinter GUI and the Telegram bot simultaneously.

---

## Building a portable `.exe` (Lenovo Legion Go)

```bat
cd installer
build_exe.bat
```

The standalone executable will be created at `dist/RickAssistant.exe`.

---

## Security

- Credentials are loaded exclusively from the `.env` file via `python-dotenv`.
- `.env` is listed in `.gitignore` and is **never committed**.
- Keep your repository **private** if it contains any secrets.
