"""Tests for charonos.integrations.telegram_bot."""

from unittest.mock import patch, MagicMock
from charonos.integrations.telegram_bot import TelegramBot


def test_not_configured():
    bot = TelegramBot(bot_token="", chat_id="")
    assert not bot.is_configured


def test_configured():
    bot = TelegramBot(bot_token="tok", chat_id="123")
    assert bot.is_configured


def test_send_message_drops_when_unconfigured():
    bot = TelegramBot(bot_token="", chat_id="")
    result = bot.send_message("hello")
    assert result == {}


def test_extract_text():
    bot = TelegramBot(bot_token="t", chat_id="1")
    update = {"message": {"text": "hi there"}}
    assert bot.extract_text(update) == "hi there"


def test_extract_text_none_when_missing():
    bot = TelegramBot(bot_token="t", chat_id="1")
    update = {"message": {}}
    assert bot.extract_text(update) is None
