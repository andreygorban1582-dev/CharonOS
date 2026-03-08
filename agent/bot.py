"""
Telegram bot handler for CharonOS.

Connects the Telegram Bot API to the LLM client and persistent memory.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from agent.llm import LLMClient
from agent.memory import PersistentMemory
from agent.tools import run_tool, REGISTRY

logger = logging.getLogger(__name__)

_TOOL_PREFIX = "/tool "


def _build_system_prompt() -> str:
    tool_names = ", ".join(REGISTRY.keys())
    base = os.getenv(
        "SYSTEM_PROMPT",
        (
            "You are CharonOS, a helpful and knowledgeable AI assistant. "
            "You remember previous conversations and can use various tools to help users. "
            "Be concise, accurate, and friendly."
        ),
    )
    return (
        f"{base}\n\n"
        f"Available tools (call via /tool <name> [args]): {tool_names}\n"
        "When the user asks you to perform a calculation or count words, "
        "instruct them to use /tool calculator or /tool word_count."
    )


class CharonBot:
    """Wraps python-telegram-bot with LLM and memory integration."""

    def __init__(
        self,
        llm: LLMClient,
        memory: PersistentMemory,
        allowed_user_ids: Optional[set[int]] = None,
    ) -> None:
        self.llm = llm
        self.memory = memory
        self.allowed_user_ids = allowed_user_ids
        self._system_prompt = _build_system_prompt()

    # ------------------------------------------------------------------
    # Permission check
    # ------------------------------------------------------------------

    def _is_allowed(self, user_id: int) -> bool:
        if not self.allowed_user_ids:
            return True
        return user_id in self.allowed_user_ids

    # ------------------------------------------------------------------
    # Command handlers
    # ------------------------------------------------------------------

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if not self._is_allowed(user.id):
            await update.message.reply_text("Sorry, you are not authorised to use this bot.")
            return
        await update.message.reply_text(
            f"Hello {user.first_name}! I'm CharonOS — an AI assistant powered by "
            "Dolphin Mistral via OpenRouter.\n\n"
            "Just send me a message and I'll reply. Type /help for more commands."
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not self._is_allowed(update.effective_user.id):
            return
        text = (
            "Commands:\n"
            "  /start — greet the bot\n"
            "  /help — show this message\n"
            "  /reset — clear your conversation history\n"
            "  /tool <name> [args] — run a built-in tool\n\n"
            "Built-in tools:\n"
            "  calculator <expression>  — e.g. /tool calculator 2+2\n"
            "  word_count <text>        — count words / chars\n"
            "  help                     — list all tools\n"
        )
        await update.message.reply_text(text)

    async def cmd_reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if not self._is_allowed(user.id):
            return
        self.memory.clear_user(user.id)
        await update.message.reply_text("Your conversation history has been cleared.")

    async def cmd_tool(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /tool <name> [args] commands."""
        user = update.effective_user
        if not self._is_allowed(user.id):
            return

        raw = update.message.text or ""
        # Strip leading "/tool " prefix
        parts = raw.split(None, 2)  # ["/tool", name, args...]
        if len(parts) < 2:
            await update.message.reply_text("Usage: /tool <name> [args]")
            return

        tool_name = parts[1].lower()
        tool_args = parts[2] if len(parts) > 2 else ""

        result = run_tool(tool_name, expression=tool_args, text=tool_args)
        await update.message.reply_text(result)

    # ------------------------------------------------------------------
    # Message handler (main LLM interaction)
    # ------------------------------------------------------------------

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        if not self._is_allowed(user.id):
            await update.message.reply_text("Sorry, you are not authorised to use this bot.")
            return

        user_text = update.message.text or ""
        if not user_text.strip():
            return

        # Show typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action=ChatAction.TYPING
        )

        # Build message list for LLM
        history = self.memory.get_history(str(user.id))
        messages: list[dict] = [{"role": "system", "content": self._system_prompt}]
        # Include prior history (role/content only — strip timestamp)
        messages += [{"role": m["role"], "content": m["content"]} for m in history]
        messages.append({"role": "user", "content": user_text})

        # Persist user message
        self.memory.add_message(str(user.id), "user", user_text)

        # Query LLM
        try:
            reply = self.llm.chat(messages)
        except Exception as exc:
            logger.exception("LLM request failed")
            await update.message.reply_text(
                f"Sorry, I encountered an error: {exc}"
            )
            return

        # Persist assistant reply
        self.memory.add_message(str(user.id), "assistant", reply)

        await update.message.reply_text(reply)

    # ------------------------------------------------------------------
    # Bot lifecycle
    # ------------------------------------------------------------------

    def build_application(self, token: str) -> Application:
        """Build and return a configured telegram Application."""
        app = Application.builder().token(token).build()

        app.add_handler(CommandHandler("start", self.cmd_start))
        app.add_handler(CommandHandler("help", self.cmd_help))
        app.add_handler(CommandHandler("reset", self.cmd_reset))
        app.add_handler(CommandHandler("tool", self.cmd_tool))
        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

        return app

    def run(self, token: str) -> None:
        """Start the bot (blocking)."""
        app = self.build_application(token)
        logger.info("CharonOS bot is running. Press Ctrl-C to stop.")
        app.run_polling(drop_pending_updates=True)
