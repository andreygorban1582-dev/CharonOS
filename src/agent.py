"""
Core AI agent.

Orchestrates OpenRouter LLM calls, injects persistent memory, and handles
special slash-commands that users can invoke from Telegram (or the CLI).
"""

from __future__ import annotations

import os
from typing import Any

from . import memory as mem
from . import openrouter

_SYSTEM_PROMPT_TEMPLATE = """\
You are CharonOS, an intelligent AI assistant. You are helpful, concise, and honest.
You remember information across conversations.

{facts}
"""


def _build_system_prompt() -> str:
    facts_block = mem.facts_as_text()
    return _SYSTEM_PROMPT_TEMPLATE.format(facts=facts_block).strip()


def _api_messages(history: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Convert stored messages (which may have extra fields) to API format."""
    return [{"role": m["role"], "content": m["content"]} for m in history]


async def handle_message(user_text: str) -> str:
    """
    Process *user_text*, update memory, call the LLM, and return the reply.

    Supports a few built-in slash-commands:
    - ``/clear``  — erase conversation history
    - ``/remember <key>=<value>``  — store a long-term fact
    - ``/facts``  — list stored facts
    - ``/help``   — list commands
    """
    text = user_text.strip()

    # --- built-in commands ---
    if text.lower() == "/clear":
        mem.clear_history()
        return "Conversation history cleared."

    if text.lower().startswith("/remember "):
        payload = text[len("/remember "):].strip()
        if "=" in payload:
            key, _, value = payload.partition("=")
            mem.save_fact(key.strip(), value.strip())
            return f"Remembered: {key.strip()} = {value.strip()}"
        return "Usage: /remember key=value"

    if text.lower() == "/facts":
        facts_text = mem.facts_as_text()
        return facts_text if facts_text else "No facts stored yet."

    if text.lower() == "/help":
        return (
            "Available commands:\n"
            "/clear — erase conversation history\n"
            "/remember key=value — store a long-term fact\n"
            "/facts — list stored facts\n"
            "/help — show this help"
        )

    # --- normal LLM turn ---
    history = mem.append_message("user", text)

    system_msg = {"role": "system", "content": _build_system_prompt()}
    api_msgs = [system_msg] + _api_messages(history)

    reply = await openrouter.chat(api_msgs)

    mem.append_message("assistant", reply)
    return reply
