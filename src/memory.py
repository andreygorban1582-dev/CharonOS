"""
Persistent memory module.

Conversation history and long-term facts are stored as JSON files inside the
``memory/`` directory so they can be committed to the repository and survive
container restarts.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_MEMORY_DIR = Path(os.environ.get("MEMORY_DIR", Path(__file__).parent.parent / "memory"))
_HISTORY_FILE = _MEMORY_DIR / "history.json"
_FACTS_FILE = _MEMORY_DIR / "facts.json"

# Maximum number of conversation turns kept in the rolling window.
MAX_HISTORY_TURNS = int(os.environ.get("MAX_HISTORY_TURNS", "50"))


def _ensure_dir() -> None:
    _MEMORY_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Conversation history
# ---------------------------------------------------------------------------


def load_history() -> list[dict[str, Any]]:
    """Return the stored message list (OpenAI format)."""
    _ensure_dir()
    if not _HISTORY_FILE.exists():
        return []
    try:
        return json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_history(messages: list[dict[str, Any]]) -> None:
    """Persist *messages* to disk, keeping only the last MAX_HISTORY_TURNS turns."""
    _ensure_dir()
    trimmed = messages[-MAX_HISTORY_TURNS * 2 :] if len(messages) > MAX_HISTORY_TURNS * 2 else messages
    _HISTORY_FILE.write_text(json.dumps(trimmed, ensure_ascii=False, indent=2), encoding="utf-8")


def append_message(role: str, content: str) -> list[dict[str, Any]]:
    """Append a single message to persisted history and return the full list."""
    messages = load_history()
    messages.append(
        {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    save_history(messages)
    return messages


def clear_history() -> None:
    """Wipe the conversation history."""
    _ensure_dir()
    _HISTORY_FILE.write_text("[]", encoding="utf-8")


# ---------------------------------------------------------------------------
# Long-term facts
# ---------------------------------------------------------------------------


def load_facts() -> dict[str, Any]:
    """Return the stored facts dictionary."""
    _ensure_dir()
    if not _FACTS_FILE.exists():
        return {}
    try:
        return json.loads(_FACTS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_fact(key: str, value: Any) -> None:
    """Store a key/value fact that persists across sessions."""
    facts = load_facts()
    facts[key] = value
    _ensure_dir()
    _FACTS_FILE.write_text(json.dumps(facts, ensure_ascii=False, indent=2), encoding="utf-8")


def get_fact(key: str, default: Any = None) -> Any:
    """Retrieve a previously stored fact."""
    return load_facts().get(key, default)


def facts_as_text() -> str:
    """Return stored facts as a human-readable string for use in system prompts."""
    facts = load_facts()
    if not facts:
        return ""
    lines = [f"- {k}: {v}" for k, v in facts.items()]
    return "Known facts about the user:\n" + "\n".join(lines)
