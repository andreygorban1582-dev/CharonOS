"""Telegram bot integration for CharonOS.

Provides both *sending* messages (proactive updates to the user) and
*polling* for incoming commands so the user can talk back to the agent.
All communication happens in a single chat identified by ``chat_id``.
"""

from __future__ import annotations

import logging
import time
from typing import Callable, Optional

import httpx

logger = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org"


class TelegramBot:
    """Telegram Bot API wrapper for CharonOS."""

    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._last_update_id: int = 0

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    # ------------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------------

    def send_message(
        self,
        text: str,
        *,
        parse_mode: str = "Markdown",
        disable_preview: bool = True,
    ) -> dict:
        """Send a message to the configured chat.  Returns the API response."""
        if not self.is_configured:
            logger.warning("Telegram not configured — message dropped: %s", text[:80])
            return {}

        url = f"{API_BASE}/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_preview,
        }

        try:
            resp = httpx.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            logger.error("Telegram send failed: %s", exc)
            return {"ok": False, "error": str(exc)}

    def send_status(self, text: str) -> dict:
        """Convenience: send a status update wrapped in Okabe formatting."""
        from charonos.personality.okabe import format_status_message

        return self.send_message(format_status_message(text))

    def send_error(self, text: str) -> dict:
        """Convenience: send an error alert wrapped in Okabe formatting."""
        from charonos.personality.okabe import format_error_message

        return self.send_message(format_error_message(text))

    def send_greeting(self) -> dict:
        """Send the boot-up greeting."""
        from charonos.personality.okabe import format_greeting

        return self.send_message(format_greeting())

    # ------------------------------------------------------------------
    # Polling (receive user messages)
    # ------------------------------------------------------------------

    def poll_updates(self, timeout: int = 30) -> list[dict]:
        """Long-poll for new messages.  Returns a list of update dicts."""
        if not self.is_configured:
            return []

        url = f"{API_BASE}/bot{self.bot_token}/getUpdates"
        params = {
            "offset": self._last_update_id + 1,
            "timeout": timeout,
            "allowed_updates": '["message"]',
        }

        try:
            resp = httpx.get(url, params=params, timeout=timeout + 10)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as exc:
            logger.error("Telegram poll failed: %s", exc)
            return []

        updates = data.get("result", [])
        if updates:
            self._last_update_id = updates[-1]["update_id"]
        return updates

    def extract_text(self, update: dict) -> Optional[str]:
        """Extract the plain text from an update dict, if present."""
        msg = update.get("message", {})
        return msg.get("text")

    # ------------------------------------------------------------------
    # Blocking listener (used by the agent main loop)
    # ------------------------------------------------------------------

    def listen(
        self,
        on_message: Callable[[str], Optional[str]],
        poll_interval: int = 1,
    ) -> None:
        """Block and listen for messages, calling *on_message* for each.

        If *on_message* returns a string, it is sent back as a reply.
        """
        logger.info("Telegram listener started (chat_id=%s)", self.chat_id)
        while True:
            updates = self.poll_updates(timeout=poll_interval)
            for update in updates:
                text = self.extract_text(update)
                if text is None:
                    continue
                logger.info("Received: %s", text[:120])
                try:
                    reply = on_message(text)
                    if reply:
                        self.send_message(reply)
                except Exception as exc:
                    logger.exception("Handler error: %s", exc)
                    self.send_error(f"Internal error: {exc}")
