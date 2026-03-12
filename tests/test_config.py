"""Tests for charonos.config."""

import os
from unittest import mock

from charonos.config import CharonConfig, TelegramConfig, OpenRouterConfig, DeepSeekConfig


def test_telegram_config_not_configured():
    cfg = TelegramConfig()
    assert not cfg.is_configured


def test_telegram_config_configured():
    cfg = TelegramConfig(bot_token="tok", chat_id="123")
    assert cfg.is_configured


def test_openrouter_config():
    cfg = OpenRouterConfig(api_key="sk-test")
    assert cfg.is_configured


def test_deepseek_config_with_api_key():
    cfg = DeepSeekConfig(api_key="sk-deep")
    assert cfg.is_configured


def test_deepseek_config_with_email():
    cfg = DeepSeekConfig(email="a@b.com", password="pw")
    assert cfg.is_configured


def test_from_env_reads_env_vars():
    env = {
        "CHARON_TELEGRAM_BOT_TOKEN": "bot-tok",
        "CHARON_TELEGRAM_CHAT_ID": "999",
        "CHARON_OPENROUTER_API_KEY": "or-key",
        "CHARON_DEEPSEEK_API_KEY": "ds-key",
        "CHARON_DEEPSEEK_EMAIL": "x@y.com",
        "CHARON_EXTRA_API_KEYS": "k1, k2, k3",
        "CHARON_EXTRA_EMAILS": "a@b.com, c@d.com",
        "CHARON_PERSONALITY": "okabe",
        "CHARON_LOG_LEVEL": "DEBUG",
    }
    with mock.patch.dict(os.environ, env, clear=False):
        cfg = CharonConfig.from_env()

    assert cfg.telegram.bot_token == "bot-tok"
    assert cfg.telegram.chat_id == "999"
    assert cfg.openrouter.api_key == "or-key"
    assert cfg.deepseek.api_key == "ds-key"
    assert cfg.extra_api_keys == ["k1", "k2", "k3"]
    assert cfg.extra_emails == ["a@b.com", "c@d.com"]
    assert cfg.personality == "okabe"


def test_total_api_keys():
    cfg = CharonConfig(
        openrouter=OpenRouterConfig(api_key="a"),
        deepseek=DeepSeekConfig(api_key="b"),
        extra_api_keys=["c", "d"],
    )
    assert cfg.total_api_keys == 4


def test_total_emails():
    cfg = CharonConfig(
        deepseek=DeepSeekConfig(email="x@y.com"),
        extra_emails=["a@b.com"],
    )
    assert cfg.total_emails == 2
