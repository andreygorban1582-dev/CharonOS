"""Core agent orchestrator for CharonOS.

Ties together every subsystem — personality, LLM backends, Telegram,
SSH cluster, ML engine, rolling context, and the growth system — into
a single cohesive agent that can be started with one call.
"""

from __future__ import annotations

import logging
import os
import re
import time
from typing import Optional

from charonos.config import CharonConfig
from charonos.context.rolling_context import RollingContext
from charonos.cluster.ssh_manager import SSHClusterManager
from charonos.growth.resource_tracker import (
    BOOTSTRAP_MODEL,
    ResourceInventory,
    Tier,
    build_inventory_from_config,
)
from charonos.growth.self_improve import GrowthEngine
from charonos.integrations.deepseek import DeepSeekClient
from charonos.integrations.openrouter import OpenRouterClient
from charonos.integrations.telegram_bot import TelegramBot
from charonos.integrations.web_automation import (
    fetch_url,
    run_local_command,
    web_search,
)
from charonos.ml.engine import IntentClassifier
from charonos.personality.okabe import (
    SIGNATURE_PHRASES,
    format_error_message,
    format_status_message,
    get_system_prompt,
)

logger = logging.getLogger(__name__)


class CharonAgent:
    """The main CharonOS agent."""

    def __init__(self, config: Optional[CharonConfig] = None) -> None:
        self.config = config or CharonConfig.from_env()

        # --- sub-systems ---
        self.inventory: ResourceInventory = build_inventory_from_config(self.config)
        self.growth: GrowthEngine = GrowthEngine(self.inventory)
        self.context: RollingContext = RollingContext(
            max_tokens=self.inventory.get_context_budget(),
        )
        self.cluster: SSHClusterManager = SSHClusterManager(
            key_dir=self.config.ssh_key_dir,
        )
        self.classifier: IntentClassifier = IntentClassifier()
        self.telegram: TelegramBot = TelegramBot(
            bot_token=self.config.telegram.bot_token,
            chat_id=self.config.telegram.chat_id,
        )

        # --- LLM clients (initialised lazily based on available keys) ---
        self._openrouter: Optional[OpenRouterClient] = None
        self._deepseek: Optional[DeepSeekClient] = None
        self._init_llm_clients()

        self._phrase_idx = 0

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------

    def _init_llm_clients(self) -> None:
        if self.config.openrouter.is_configured:
            # Use the tier-appropriate model, defaulting to Dolphin Mistral
            model = self.inventory.get_recommended_model() or BOOTSTRAP_MODEL
            self._openrouter = OpenRouterClient(
                api_key=self.config.openrouter.api_key,
                default_model=model,
            )
        if self.config.deepseek.api_key:
            self._deepseek = DeepSeekClient(api_key=self.config.deepseek.api_key)

    # ------------------------------------------------------------------
    # LLM interaction
    # ------------------------------------------------------------------

    def _llm_chat(self, user_message: str) -> str:
        """Send the rolling context + new message to the best available LLM."""
        self.context.add("user", user_message)
        messages = self.context.get_context(system_prompt=get_system_prompt())

        reply: Optional[str] = None

        # Try OpenRouter first (it routes to the tier-appropriate model)
        if self._openrouter and self._openrouter.is_configured:
            try:
                reply = self._openrouter.chat(messages)
            except Exception as exc:
                logger.warning("OpenRouter failed, trying fallback: %s", exc)

        # Fallback to DeepSeek direct
        if reply is None and self._deepseek and self._deepseek.is_configured:
            try:
                reply = self._deepseek.chat(messages)
            except Exception as exc:
                logger.warning("DeepSeek failed: %s", exc)

        if reply is None:
            reply = self._local_fallback(user_message)

        self.context.add("assistant", reply)
        return reply

    def _local_fallback(self, user_message: str) -> str:
        """When no LLM is available, handle commands locally."""
        intent = self.classifier.predict(user_message)
        return self._handle_intent(intent, user_message)

    # ------------------------------------------------------------------
    # Intent handling (works with or without an LLM)
    # ------------------------------------------------------------------

    def _handle_intent(self, intent: str, raw: str) -> str:
        handlers = {
            "status": self._cmd_status,
            "cluster": self._cmd_cluster,
            "growth": self._cmd_growth,
            "help": self._cmd_help,
            "greeting": self._cmd_greeting,
            "config": lambda _r: self._cmd_config(_r),
            "execute": lambda _r: self._cmd_execute(_r),
        }
        handler = handlers.get(intent, self._cmd_unknown)
        return handler(raw)

    def _cmd_status(self, _raw: str) -> str:
        tier = self.growth.current_tier
        model = self.inventory.get_recommended_model() or "local-only"
        return format_status_message(
            f"Tier: *{tier.name}* (level {tier.value})\n"
            f"Model: `{model}`\n"
            f"Context: {self.context.estimate_tokens():,} tokens active, "
            f"{self.context.total_messages_ever} messages total\n"
            f"API keys: {len(self.inventory.api_keys)} | "
            f"SSH nodes: {len(self.inventory.ssh_hosts)} | "
            f"Emails: {len(self.inventory.emails)}\n"
            f"{self.cluster.cluster_status()}"
        )

    def _cmd_cluster(self, _raw: str) -> str:
        return format_status_message(self.cluster.cluster_status())

    def _cmd_growth(self, _raw: str) -> str:
        return format_status_message(self.growth.get_growth_report())

    def _cmd_greeting(self, _raw: str) -> str:
        phrase = SIGNATURE_PHRASES[self._phrase_idx % len(SIGNATURE_PHRASES)]
        self._phrase_idx += 1
        return (
            f"Ah, Lab Mem 002!  You've returned.  {phrase}\n\n"
            "Type /help to see what experiments we can run."
        )

    def _cmd_help(self, _raw: str) -> str:
        return (
            "🔬 *CharonOS — Command Reference*\n\n"
            "/status  — Current agent status & tier\n"
            "/cluster — Cluster node overview\n"
            "/growth  — Growth report & tier details\n"
            "/search <query> — Search the web\n"
            "/fetch <url> — Fetch & read a web page\n"
            "/run <cmd> — Execute a local command\n"
            "/addkey <key> — Register a new API key\n"
            "/addssh <host> — Add an SSH node\n"
            "/addemail <email> — Register an email\n"
            "/help — This message\n\n"
            "_El Psy Kongroo._"
        )

    def _cmd_config(self, raw: str) -> str:
        return "Configuration command noted. Use /addkey, /addssh, or /addemail."

    def _cmd_execute(self, raw: str) -> str:
        return "Use /run <command> to execute a command."

    def _cmd_unknown(self, raw: str) -> str:
        return f"Hmm, the divergence meter is unclear on that one. Try /help."

    # ------------------------------------------------------------------
    # Telegram slash-command router
    # ------------------------------------------------------------------

    def handle_message(self, text: str) -> str:
        """Route an incoming Telegram message and return a reply string."""
        text = text.strip()

        # Slash commands
        if text.startswith("/"):
            return self._handle_slash(text)

        # If we have an LLM, use it for free-form chat
        if self._openrouter or self._deepseek:
            return self._llm_chat(text)

        # Otherwise fall back to intent classification
        intent = self.classifier.predict(text)
        return self._handle_intent(intent, text)

    def _handle_slash(self, text: str) -> str:
        parts = text.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "/status":
            return self._cmd_status(arg)
        if cmd == "/cluster":
            return self._cmd_cluster(arg)
        if cmd == "/growth":
            return self._cmd_growth(arg)
        if cmd == "/help":
            return self._cmd_help(arg)
        if cmd == "/search":
            return self._do_search(arg)
        if cmd == "/fetch":
            return self._do_fetch(arg)
        if cmd == "/run":
            return self._do_run(arg)
        if cmd == "/addkey":
            return self._do_add_key(arg)
        if cmd == "/addssh":
            return self._do_add_ssh(arg)
        if cmd == "/addemail":
            return self._do_add_email(arg)

        # Unknown slash → try LLM or fallback
        if self._openrouter or self._deepseek:
            return self._llm_chat(text)
        return self._cmd_unknown(text)

    # ------------------------------------------------------------------
    # Action commands
    # ------------------------------------------------------------------

    def _do_search(self, query: str) -> str:
        if not query:
            return "Usage: /search <query>"
        results = web_search(query, max_results=5)
        if not results:
            return format_status_message("The Organization has hidden the results… no matches found.")
        lines = [f"🔎 *Web search: {query}*\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. [{r.title}]({r.url})\n   {r.snippet}\n")
        lines.append("\n_El Psy Kongroo._")
        return "\n".join(lines)

    def _do_fetch(self, url: str) -> str:
        if not url:
            return "Usage: /fetch <url>"
        body = fetch_url(url.strip(), max_length=3000)
        return f"📄 *Fetched content:*\n```\n{body[:3000]}\n```"

    def _do_run(self, command: str) -> str:
        if not command:
            return "Usage: /run <command>"
        output = run_local_command(command, timeout=60)
        return f"⚙️ *Command output:*\n```\n{output[:3500]}\n```"

    def _do_add_key(self, key: str) -> str:
        key = key.strip()
        if not key:
            return "Usage: /addkey <api-key>"
        self.inventory.add_api_key(key)
        evt = self.growth.check_for_upgrade()
        msg = f"API key registered.  Total keys: {len(self.inventory.api_keys)}."
        if evt:
            msg += f"\n\n🚀 *{evt.description}*"
            self.context.max_tokens = self.inventory.get_context_budget()
            self._init_llm_clients()
        return format_status_message(msg)

    def _do_add_ssh(self, host: str) -> str:
        host = host.strip()
        if not host:
            return "Usage: /addssh <host>"
        self.cluster.add_node(host)
        self.inventory.add_ssh_host(host)
        evt = self.growth.check_for_upgrade()
        msg = f"SSH node `{host}` added.  Cluster size: {self.cluster.node_count}."
        if evt:
            msg += f"\n\n🚀 *{evt.description}*"
            self.context.max_tokens = self.inventory.get_context_budget()
        return format_status_message(msg)

    def _do_add_email(self, email: str) -> str:
        email = email.strip()
        if not email:
            return "Usage: /addemail <email>"
        self.inventory.add_email(email)
        msg = f"Email registered.  Total emails: {len(self.inventory.emails)}."
        return format_status_message(msg)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the agent: send greeting, then listen on Telegram forever."""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level, logging.INFO),
            format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        )
        logger.info(
            "CharonOS starting — Tier %s (%s)",
            self.growth.current_tier.value,
            self.growth.current_tier.name,
        )

        # Send boot greeting
        if self.telegram.is_configured:
            self.telegram.send_greeting()
            self.telegram.send_status(self.growth.get_growth_report())
            logger.info("Greeting sent via Telegram.  Entering listen loop.")
            self.telegram.listen(self.handle_message)
        else:
            logger.warning(
                "Telegram not configured.  Set CHARON_TELEGRAM_BOT_TOKEN and "
                "CHARON_TELEGRAM_CHAT_ID in your .env file."
            )
            print("⚠️  Telegram not configured — running in local REPL mode.")
            print("Type messages below (Ctrl+C to quit):\n")
            self._repl()

    def _repl(self) -> None:
        """Simple stdin REPL for when Telegram is not configured."""
        try:
            while True:
                user_input = input("You> ")
                reply = self.handle_message(user_input)
                print(f"Hououin Kyouma> {reply}\n")
        except (KeyboardInterrupt, EOFError):
            print("\nEl Psy Kongroo.")
