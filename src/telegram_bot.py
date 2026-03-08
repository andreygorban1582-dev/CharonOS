"""
Telegram bot interface for the CharonOS AI agent.

Start with:
    python -m src.telegram_bot

Requires the ``TELEGRAM_BOT_TOKEN`` environment variable.
"""

from __future__ import annotations

import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from . import agent

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def _start(update: Update, _ctx) -> None:
    await update.message.reply_text(
        "👋 Hello! I'm CharonOS AI. Ask me anything, or type `/help` to see available commands."
    )


async def _handle_text(update: Update, _ctx) -> None:
    user_input = update.message.text or ""
    logger.info("User %s: %s", update.effective_user.id, user_input[:80])

    await update.message.chat.send_action("typing")
    reply = await agent.handle_message(user_input)
    await update.message.reply_text(reply)


async def _handle_command(update: Update, _ctx) -> None:
    """Forward slash-commands to the agent so /clear, /remember etc. work."""
    text = update.message.text or ""
    await update.message.chat.send_action("typing")
    reply = await agent.handle_message(text)
    await update.message.reply_text(reply)


def run() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set.")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", _start))
    # Forward agent slash-commands
    for cmd in ("clear", "remember", "facts", "help"):
        app.add_handler(CommandHandler(cmd, _handle_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_text))

    logger.info("CharonOS Telegram bot is running…")
    app.run_polling()


if __name__ == "__main__":
    run()
