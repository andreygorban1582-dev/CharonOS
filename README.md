# CharonOS

A self-contained AI agent that runs entirely in **GitHub Codespaces**.

## Features

| Feature | Details |
|---|---|
| 🤖 **LLM** | Dolphin Mistral (primary) via [OpenRouter](https://openrouter.ai), with automatic multi-model fallback |
| 🔑 **Multi-key support** | Round-robin across multiple OpenRouter API keys for load balancing and redundancy |
| 💬 **Telegram bot** | Full conversation interface via `/start`, `/help`, `/reset`, `/tool` commands |
| 🧠 **Persistent memory** | Per-user conversation history stored as JSON files, committed back to this repo automatically |
| 🛠️ **Built-in tools** | Calculator, word counter, extensible tool registry |
| 🐳 **Codespaces-ready** | One-click dev environment via `.devcontainer/` |

---

## Quick Start in GitHub Codespaces

1. Open this repository in GitHub Codespaces (click **Code → Codespaces → Create codespace**).  
   The post-create script installs all dependencies and creates a `.env` file.

2. Edit `.env` with your credentials:

   ```env
   TELEGRAM_BOT_TOKEN=<your bot token from @BotFather>
   OPENROUTER_API_KEY=<your key from https://openrouter.ai/keys>
   ```

3. Run the agent:

   ```bash
   python -m agent.main
   ```

---

## Configuration

Copy `.env.example` to `.env` and fill in the values:

| Variable | Required | Default | Description |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | — | Token from [@BotFather](https://t.me/BotFather) |
| `OPENROUTER_API_KEY` | ✅ | — | Primary OpenRouter API key |
| `OPENROUTER_EXTRA_KEYS` | ❌ | — | Comma-separated extra keys for round-robin balancing |
| `PRIMARY_MODEL` | ❌ | `cognitivecomputations/dolphin-mistral-24gb` | Primary LLM model |
| `FALLBACK_MODELS` | ❌ | see `.env.example` | Comma-separated fallback models |
| `ALLOWED_USER_IDS` | ❌ | all | Comma-separated Telegram user IDs that may use the bot |
| `MAX_HISTORY_PER_USER` | ❌ | `50` | Max conversation messages kept per user |
| `MEMORY_COMMIT_EVERY` | ❌ | `5` | Commit memory to GitHub every N messages |
| `SYSTEM_PROMPT` | ❌ | built-in | Override the system prompt |

### Supported OpenRouter models (examples)

```
cognitivecomputations/dolphin-mistral-24gb   ← default (Dolphin Mistral)
mistralai/mistral-7b-instruct
nousresearch/nous-hermes-2-mixtral-8x7b-dpo
meta-llama/llama-3.1-8b-instruct:free
```

Full list at <https://openrouter.ai/models>.

---

## Architecture

```
CharonOS/
├── .devcontainer/
│   ├── devcontainer.json   ← Codespaces container definition
│   └── setup.sh            ← Post-create install script
├── agent/
│   ├── main.py             ← Entry point
│   ├── bot.py              ← Telegram bot (python-telegram-bot)
│   ├── llm.py              ← OpenRouter client (multi-key, multi-model)
│   ├── memory.py           ← Persistent memory (JSON → GitHub commit)
│   └── tools.py            ← Built-in tools (calculator, word_count …)
├── memory/
│   ├── conversations.json  ← Per-user chat history (auto-committed)
│   └── facts.json          ← Key/value facts (auto-committed)
├── tests/                  ← pytest test suite
├── .env.example
├── .gitignore
└── requirements.txt
```

### Persistent memory flow

```
User message
     │
     ▼
PersistentMemory.add_message()
     │
     ├─ writes conversations.json + facts.json
     │
     └─ every MEMORY_COMMIT_EVERY messages:
          git add → git commit → git push  (to this repo)
```

---

## Telegram commands

| Command | Description |
|---|---|
| `/start` | Greeting message |
| `/help` | Show available commands and tools |
| `/reset` | Clear your personal conversation history |
| `/tool calculator <expr>` | Evaluate a math expression |
| `/tool word_count <text>` | Count words and characters |
| `/tool help` | List all built-in tools |

---

## Running tests

```bash
python -m pytest tests/ -v
```

---

## Extending the agent

### Add a new tool

Edit `agent/tools.py`:

```python
def my_tool(text: str, **_) -> str:
    """One-line description shown in /tool help."""
    return text.upper()

REGISTRY["my_tool"] = my_tool
```

The tool is immediately available via `/tool my_tool <args>`.

### Add another OpenRouter API key

```env
OPENROUTER_EXTRA_KEYS=sk-or-key2,sk-or-key3
```

Requests are distributed round-robin across all keys.
