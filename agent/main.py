"""
CharonOS AI Agent — entry point.

Usage (from the repo root):
    python -m agent.main

Environment variables are loaded from .env automatically.
"""

from __future__ import annotations

import logging
import os
import sys

from dotenv import load_dotenv

# Load .env before importing anything that reads env vars
load_dotenv()

from agent.llm import LLMClient
from agent.memory import PersistentMemory
from agent.bot import CharonBot


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _parse_allowed_ids() -> set[int] | None:
    raw = os.getenv("ALLOWED_USER_IDS", "").strip()
    if not raw:
        return None
    try:
        return {int(uid.strip()) for uid in raw.split(",") if uid.strip()}
    except ValueError as exc:
        logging.getLogger(__name__).error(
            "ALLOWED_USER_IDS contains non-integer values: %s", exc
        )
        sys.exit(1)


def main() -> None:
    _setup_logging()
    log = logging.getLogger(__name__)

    # ── Validate required environment variables ───────────────────────────────
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        log.error(
            "TELEGRAM_BOT_TOKEN is not set. "
            "Copy .env.example to .env and fill in your credentials."
        )
        sys.exit(1)

    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    if not openrouter_key:
        log.error(
            "OPENROUTER_API_KEY is not set. "
            "Copy .env.example to .env and fill in your credentials."
        )
        sys.exit(1)

    # ── Initialise components ─────────────────────────────────────────────────
    log.info("Initialising LLM client (OpenRouter)...")
    llm = LLMClient()

    log.info("Initialising persistent memory...")
    memory = PersistentMemory()

    allowed_ids = _parse_allowed_ids()
    if allowed_ids:
        log.info("Access restricted to %d user(s).", len(allowed_ids))
    else:
        log.info("No user restriction — all Telegram users may interact.")

    # ── Start bot ─────────────────────────────────────────────────────────────
    bot = CharonBot(llm=llm, memory=memory, allowed_user_ids=allowed_ids)
    log.info("Starting CharonOS Telegram bot...")
    bot.run(token)


if __name__ == "__main__":
    main()
