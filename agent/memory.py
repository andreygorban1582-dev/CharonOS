"""
Persistent memory for CharonOS.

Conversation history and extracted facts are stored as JSON files inside the
``memory/`` directory of this repository.  After every MEMORY_COMMIT_EVERY
new messages the changes are committed and pushed back to GitHub so that
context survives across Codespace restarts.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import git

logger = logging.getLogger(__name__)

_DEFAULT_MAX_HISTORY = 50
_DEFAULT_COMMIT_EVERY = 5


class PersistentMemory:
    """Per-user conversation history with GitHub-backed persistence."""

    def __init__(
        self,
        repo_path: str | None = None,
        max_history_per_user: int | None = None,
        commit_every: int | None = None,
    ) -> None:
        self.repo_path = Path(repo_path or os.getenv("REPO_PATH", ".")).resolve()
        self.memory_dir = self.repo_path / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        self.max_history: int = max_history_per_user or int(
            os.getenv("MAX_HISTORY_PER_USER", str(_DEFAULT_MAX_HISTORY))
        )
        self.commit_every: int = commit_every or int(
            os.getenv("MEMORY_COMMIT_EVERY", str(_DEFAULT_COMMIT_EVERY))
        )

        # Paths
        self._conv_file = self.memory_dir / "conversations.json"
        self._facts_file = self.memory_dir / "facts.json"

        # In-memory state
        self._conversations: dict[str, list[dict]] = {}
        self._facts: dict[str, Any] = {}
        self._message_counter: int = 0

        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_history(self, user_id: str) -> list[dict]:
        """Return the message history for *user_id* as a list of role/content dicts."""
        return list(self._conversations.get(str(user_id), []))

    def add_message(self, user_id: str, role: str, content: str) -> None:
        """Append a message to the user's history and maybe persist."""
        uid = str(user_id)
        if uid not in self._conversations:
            self._conversations[uid] = []

        self._conversations[uid].append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        # Trim to keep only the most recent messages
        self._conversations[uid] = self._conversations[uid][-self.max_history :]

        self._message_counter += 1
        if self._message_counter % self.commit_every == 0:
            self.save(commit=True)

    def set_fact(self, key: str, value: Any) -> None:
        """Store an arbitrary fact (e.g. user preference)."""
        self._facts[key] = value

    def get_fact(self, key: str, default: Any = None) -> Any:
        return self._facts.get(key, default)

    def save(self, commit: bool = True) -> None:
        """Write memory to disk and optionally commit/push to GitHub."""
        self._write_files()
        if commit:
            self._commit_and_push()

    def clear_user(self, user_id: str) -> None:
        """Erase the conversation history for a single user."""
        self._conversations.pop(str(user_id), None)
        self.save(commit=True)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if self._conv_file.exists():
            try:
                with open(self._conv_file, encoding="utf-8") as fh:
                    self._conversations = json.load(fh)
            except json.JSONDecodeError:
                logger.warning("conversations.json is corrupt; starting fresh.")
                self._conversations = {}

        if self._facts_file.exists():
            try:
                with open(self._facts_file, encoding="utf-8") as fh:
                    self._facts = json.load(fh)
            except json.JSONDecodeError:
                logger.warning("facts.json is corrupt; starting fresh.")
                self._facts = {}

    def _write_files(self) -> None:
        with open(self._conv_file, "w", encoding="utf-8") as fh:
            json.dump(self._conversations, fh, indent=2, ensure_ascii=False)
        with open(self._facts_file, "w", encoding="utf-8") as fh:
            json.dump(self._facts, fh, indent=2, ensure_ascii=False)

    def _commit_and_push(self) -> None:
        try:
            repo = git.Repo(self.repo_path)
            rel_conv = str(self._conv_file.relative_to(self.repo_path))
            rel_facts = str(self._facts_file.relative_to(self.repo_path))
            repo.index.add([rel_conv, rel_facts])
            if repo.is_dirty(index=True):
                stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                repo.index.commit(f"chore(memory): update context [{stamp}]")
                repo.remotes.origin.push()
                logger.info("Memory committed and pushed to GitHub.")
            else:
                logger.debug("Memory unchanged; skipping commit.")
        except Exception as exc:
            logger.warning("Could not persist memory to GitHub: %s", exc)
