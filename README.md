# CharonOS

> *"I am the mad scientist, Hououin Kyouma!  CharonOS is the choice of Steins Gate!"*

**CharonOS** is an autonomous AI agent that runs in a GitHub Codespace, communicates with you via Telegram, and **grows itself** by upgrading to larger language models as you give it more resources.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Okabe Rintaro personality** | The agent speaks as Hououin Kyouma from *Steins;Gate* — dramatic flair, "El Psy Kongroo," lab member numbering, and all. |
| **Dynamic LLM growth** | Starts on **Dolphin Mistral** (Tier 1) and automatically upgrades to DeepSeek, Llama 405B, GPT-4o, or Claude as you add API keys & SSH nodes. |
| **Telegram-first interface** | All interaction happens through a Telegram bot — status updates, commands, and free-form chat. |
| **Compute cluster** | SSH-based cluster manager — add codespace nodes at runtime with `/addssh`. |
| **Web search & automation** | Search the web (`/search`), fetch pages (`/fetch`), and run local commands (`/run`). |
| **Rolling context** | Unlimited conversation memory via rolling compaction — old messages are summarised so context never overflows. |
| **ML intent classifier** | On-device scikit-learn classifier that learns your command patterns over time. |
| **Auto-start in Codespace** | The `.devcontainer` is configured to install deps and launch the agent when you open the Codespace. |

---

## 🏗 Architecture

```
charonos/
├── agent.py                    # Core orchestrator — ties everything together
├── config.py                   # Env-based configuration (secrets from .env)
├── personality/
│   └── okabe.py                # Hououin Kyouma system prompt & formatting
├── context/
│   └── rolling_context.py      # Unlimited rolling context window
├── growth/
│   ├── resource_tracker.py     # Tier system & resource inventory
│   └── self_improve.py         # Growth engine — detects & logs upgrades
├── cluster/
│   └── ssh_manager.py          # SSH cluster node management
├── integrations/
│   ├── openrouter.py           # OpenRouter LLM client
│   ├── deepseek.py             # DeepSeek API client
│   ├── telegram_bot.py         # Telegram send/receive/listen
│   └── web_automation.py       # Web search, URL fetch, command execution
└── ml/
    └── engine.py               # TF-IDF + SGD intent classifier
```

## 🚀 Quick Start (Codespace)

1. **Fork / clone** this repository.
2. **Set Codespace secrets** (Settings → Codespaces → Secrets):

   | Secret | Description |
   |---|---|
   | `CHARON_TELEGRAM_BOT_TOKEN` | Telegram bot token from [@BotFather](https://t.me/BotFather) |
   | `CHARON_TELEGRAM_CHAT_ID` | Your Telegram user/chat ID |
   | `CHARON_OPENROUTER_API_KEY` | OpenRouter API key (starts agent at Tier 1) |
   | `CHARON_DEEPSEEK_API_KEY` | *(optional)* DeepSeek API key |

3. **Open a Codespace** — the agent installs itself and starts automatically.
4. **Open Telegram** — you'll see the boot greeting from Hououin Kyouma.

### Local / manual start

```bash
pip install -e '.[dev]'
cp .env.example .env   # edit with your credentials
python -m scripts.start_agent
```

---

## 📡 Telegram Commands

| Command | What it does |
|---|---|
| `/status` | Current tier, model, context stats, cluster info |
| `/growth` | Detailed growth report |
| `/cluster` | SSH cluster node list |
| `/search <query>` | Web search via DuckDuckGo |
| `/fetch <url>` | Fetch and display a web page |
| `/run <command>` | Execute a local shell command |
| `/addkey <key>` | Register a new API key (may trigger tier upgrade!) |
| `/addssh <host>` | Add an SSH compute node |
| `/addemail <email>` | Register an email account |
| `/help` | Show all commands |

Any non-command message is sent to the LLM as free-form chat (or handled by the intent classifier if no LLM is available).

---

## 📈 Growth Tiers

The agent upgrades automatically as you give it resources:

| Tier | Requirements | Model | Context |
|---|---|---|---|
| **0 — LOCAL** | No API keys | *(local intent classifier only)* | 2k tokens |
| **1 — SMALL** | 1 API key | Dolphin Mistral | 8k tokens |
| **2 — MEDIUM** | 2+ keys or 1+ SSH node | DeepSeek Chat | 32k tokens |
| **3 — FRONTIER** | 4+ keys and 2+ SSH nodes | DeepSeek / Claude / GPT-4o | 128k tokens |

---

## 🧪 Tests

```bash
pip install -e '.[dev]'
pytest tests/ -v
```

---

## 📜 License

MIT