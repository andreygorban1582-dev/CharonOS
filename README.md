# CharonOS

An AI agent that runs entirely in GitHub Codespaces, powered by LLMs via
[OpenRouter](https://openrouter.ai) and connected to Telegram for a chat
interface. Conversation history and long-term facts are persisted inside the
repository so context survives container restarts.

---

## Features

- **LLM via OpenRouter** — use any model available on the platform (defaults to
  `mistralai/mistral-7b-instruct`; easily swapped for Dolphin-Mistral,
  GPT-4o, Claude, etc.)
- **Telegram bot** — full chat interface with slash-commands
- **Persistent memory** — conversation history and user facts stored as JSON in
  the `memory/` directory and committed to GitHub
- **CLI mode** — run an interactive session from the terminal without Telegram
- **Codespaces-ready** — `.devcontainer/devcontainer.json` sets up the
  environment automatically

---

## Quick Start

### 1. Open in Codespaces

Click **Code → Open with Codespaces** on GitHub.  The devcontainer will install
all Python dependencies automatically.

### 2. Configure environment variables

```bash
cp .env.example .env
# Then edit .env and fill in the required values:
#   OPENROUTER_API_KEY  — from https://openrouter.ai/keys
#   TELEGRAM_BOT_TOKEN  — from @BotFather on Telegram
#   OPENROUTER_MODEL    — optional, defaults to mistralai/mistral-7b-instruct
```

### 3. Run

**Telegram bot mode (default):**
```bash
python main.py
```

**Interactive CLI mode:**
```bash
python main.py --cli
```

---

## Slash-commands

| Command | Description |
|---|---|
| `/start` | Greeting message |
| `/help` | List available commands |
| `/clear` | Erase conversation history |
| `/remember key=value` | Store a long-term fact |
| `/facts` | List all stored facts |

---

## Choosing a model

Set `OPENROUTER_MODEL` in `.env` to any model string from
[openrouter.ai/models](https://openrouter.ai/models).

Examples:
```
OPENROUTER_MODEL=cognitivecomputations/dolphin-mistral-7b
OPENROUTER_MODEL=openai/gpt-4o
OPENROUTER_MODEL=anthropic/claude-3-haiku
```

---

## Project structure

```
CharonOS/
├── main.py                  # Entry point
├── requirements.txt
├── .env.example             # Template for secrets
├── .devcontainer/
│   └── devcontainer.json    # Codespaces configuration
├── memory/
│   ├── history.json         # Rolling conversation history (git-tracked)
│   └── facts.json           # Long-term facts (git-tracked)
└── src/
    ├── __init__.py
    ├── agent.py             # Core agent logic & slash-command handling
    ├── memory.py            # Persistent memory (read/write JSON)
    ├── openrouter.py        # OpenRouter API client
    └── telegram_bot.py      # Telegram bot runner
```

---

## Running tests

```bash
pip install pytest pytest-asyncio
pytest tests/
```