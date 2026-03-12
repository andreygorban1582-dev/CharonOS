"""Rolling context manager for CharonOS.

Implements an unlimited rolling context window that keeps the most recent
messages within the LLM's token budget while preserving a persistent
summary of older context.  This gives the agent effectively unbounded
memory across conversations.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Message:
    """A single message in the conversation."""

    role: str  # "system" | "user" | "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


class RollingContext:
    """Manages a rolling context window with summary compaction.

    Parameters
    ----------
    max_tokens : int
        Soft token budget for the active context window.  When exceeded
        the oldest messages are compacted into a running summary.
    chars_per_token : int
        Rough character-to-token ratio used for estimation (default 4).
    """

    def __init__(
        self,
        max_tokens: int = 8_000,
        chars_per_token: int = 4,
        persist_path: Optional[str] = None,
    ) -> None:
        self.max_tokens = max_tokens
        self.chars_per_token = chars_per_token
        self.persist_path = persist_path

        self._summary: str = ""
        self._messages: list[Message] = []
        self._total_messages_ever: int = 0

        if persist_path:
            self._load(persist_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, role: str, content: str) -> None:
        """Append a new message and compact if over budget."""
        self._messages.append(Message(role=role, content=content))
        self._total_messages_ever += 1
        self._maybe_compact()

    def get_context(self, system_prompt: str = "") -> list[dict]:
        """Return the message list suitable for an LLM API call.

        The returned list always starts with the system prompt (if given),
        followed by a summary message (if any prior context was compacted),
        then the active message window.
        """
        ctx: list[dict] = []
        if system_prompt:
            ctx.append({"role": "system", "content": system_prompt})
        if self._summary:
            ctx.append(
                {
                    "role": "system",
                    "content": (
                        f"[Conversation summary so far]\n{self._summary}"
                    ),
                }
            )
        ctx.extend(m.to_dict() for m in self._messages)
        return ctx

    @property
    def summary(self) -> str:
        return self._summary

    @property
    def active_message_count(self) -> int:
        return len(self._messages)

    @property
    def total_messages_ever(self) -> int:
        return self._total_messages_ever

    def estimate_tokens(self) -> int:
        """Estimate the token count of the active window."""
        total_chars = sum(len(m.content) for m in self._messages)
        total_chars += len(self._summary)
        return total_chars // self.chars_per_token

    def save(self, path: Optional[str] = None) -> None:
        """Persist context to disk."""
        target = path or self.persist_path
        if not target:
            return
        data = {
            "summary": self._summary,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp,
                }
                for m in self._messages
            ],
            "total_messages_ever": self._total_messages_ever,
        }
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        Path(target).write_text(json.dumps(data, indent=2))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self, path: str) -> None:
        p = Path(path)
        if not p.is_file():
            return
        data = json.loads(p.read_text())
        self._summary = data.get("summary", "")
        self._total_messages_ever = data.get("total_messages_ever", 0)
        for m in data.get("messages", []):
            self._messages.append(
                Message(
                    role=m["role"],
                    content=m["content"],
                    timestamp=m.get("timestamp", 0.0),
                )
            )

    def _maybe_compact(self) -> None:
        """If the window is over budget, fold the oldest half into the summary."""
        if self.estimate_tokens() <= self.max_tokens:
            return

        # Keep the newest half
        mid = len(self._messages) // 2
        old = self._messages[:mid]
        self._messages = self._messages[mid:]

        # Build a concise summary of the compacted messages
        compacted_text = "\n".join(
            f"{m.role}: {m.content[:200]}" for m in old
        )
        if self._summary:
            self._summary = (
                f"{self._summary}\n---\n"
                f"[Compacted {len(old)} older messages]\n{compacted_text}"
            )
        else:
            self._summary = (
                f"[Compacted {len(old)} messages]\n{compacted_text}"
            )
