"""Configuration management for CharonOS.

Loads credentials and settings from environment variables and .env files.
All secrets are read from the environment — never hardcoded.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field


def _load_env() -> None:
    """Load .env file from the project root if it exists."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.is_file():
        load_dotenv(env_path, override=False)


_load_env()


class TelegramConfig(BaseModel):
    """Telegram bot settings."""

    bot_token: str = Field(default="")
    chat_id: str = Field(default="")

    @property
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)


class OpenRouterConfig(BaseModel):
    """OpenRouter API settings."""

    api_key: str = Field(default="")
    base_url: str = Field(default="https://openrouter.ai/api/v1")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


class DeepSeekConfig(BaseModel):
    """DeepSeek account settings."""

    email: str = Field(default="")
    password: str = Field(default="")
    api_key: str = Field(default="")
    base_url: str = Field(default="https://api.deepseek.com")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key) or bool(self.email and self.password)


class CharonConfig(BaseModel):
    """Top-level configuration for the CharonOS agent."""

    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    openrouter: OpenRouterConfig = Field(default_factory=OpenRouterConfig)
    deepseek: DeepSeekConfig = Field(default_factory=DeepSeekConfig)

    extra_api_keys: list[str] = Field(default_factory=list)
    extra_emails: list[str] = Field(default_factory=list)

    personality: str = Field(default="okabe")
    log_level: str = Field(default="INFO")

    ssh_key_dir: str = Field(default="~/.ssh")

    @classmethod
    def from_env(cls) -> "CharonConfig":
        """Build configuration from environment variables."""
        _load_env()

        extra_keys_raw = os.getenv("CHARON_EXTRA_API_KEYS", "")
        extra_keys = [k.strip() for k in extra_keys_raw.split(",") if k.strip()]

        extra_emails_raw = os.getenv("CHARON_EXTRA_EMAILS", "")
        extra_emails = [e.strip() for e in extra_emails_raw.split(",") if e.strip()]

        return cls(
            telegram=TelegramConfig(
                bot_token=os.getenv("CHARON_TELEGRAM_BOT_TOKEN", ""),
                chat_id=os.getenv("CHARON_TELEGRAM_CHAT_ID", ""),
            ),
            openrouter=OpenRouterConfig(
                api_key=os.getenv("CHARON_OPENROUTER_API_KEY", ""),
            ),
            deepseek=DeepSeekConfig(
                email=os.getenv("CHARON_DEEPSEEK_EMAIL", ""),
                password=os.getenv("CHARON_DEEPSEEK_PASSWORD", ""),
                api_key=os.getenv("CHARON_DEEPSEEK_API_KEY", ""),
            ),
            extra_api_keys=extra_keys,
            extra_emails=extra_emails,
            personality=os.getenv("CHARON_PERSONALITY", "okabe"),
            log_level=os.getenv("CHARON_LOG_LEVEL", "INFO"),
            ssh_key_dir=os.getenv("CHARON_SSH_KEY_DIR", "~/.ssh"),
        )

    # ------------------------------------------------------------------
    # Resource accounting — used by the growth / tier system
    # ------------------------------------------------------------------

    @property
    def total_api_keys(self) -> int:
        count = 0
        if self.openrouter.is_configured:
            count += 1
        if self.deepseek.api_key:
            count += 1
        count += len(self.extra_api_keys)
        return count

    @property
    def total_emails(self) -> int:
        count = 0
        if self.deepseek.email:
            count += 1
        count += len(self.extra_emails)
        return count
