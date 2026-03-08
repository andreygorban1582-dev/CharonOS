"""Tests for agent.llm"""
import pytest
from unittest.mock import MagicMock, patch, call

from agent.llm import LLMClient


def _make_response(content: str):
    """Build a mock OpenAI-style response object."""
    choice = MagicMock()
    choice.message.content = content
    response = MagicMock()
    response.choices = [choice]
    return response


class TestLLMClient:
    def test_chat_returns_content(self):
        with patch("agent.llm.OpenAI") as MockOpenAI:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = _make_response("Hello!")
            MockOpenAI.return_value = mock_client

            llm = LLMClient(api_keys=["fake-key"])
            result = llm.chat([{"role": "user", "content": "Hi"}])

        assert result == "Hello!"

    def test_fallback_on_error(self):
        from openai import APIConnectionError

        with patch("agent.llm.OpenAI") as MockOpenAI:
            mock_client = MagicMock()
            # First call (primary model) raises; second (fallback) succeeds
            mock_client.chat.completions.create.side_effect = [
                Exception("primary failed"),
                _make_response("fallback response"),
            ]
            MockOpenAI.return_value = mock_client

            llm = LLMClient(
                api_keys=["fake-key"],
                primary_model="primary-model",
                fallback_models=["fallback-model"],
            )
            result = llm.chat([{"role": "user", "content": "Hi"}])

        assert result == "fallback response"

    def test_all_models_fail_raises(self):
        with patch("agent.llm.OpenAI") as MockOpenAI:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = Exception("boom")
            MockOpenAI.return_value = mock_client

            llm = LLMClient(
                api_keys=["fake-key"],
                primary_model="m1",
                fallback_models=["m2"],
            )
            with pytest.raises(RuntimeError, match="All models failed"):
                llm.chat([{"role": "user", "content": "Hi"}])

    def test_multiple_api_keys_round_robin(self):
        """Subsequent requests cycle through available clients."""
        with patch("agent.llm.OpenAI") as MockOpenAI:
            clients = [MagicMock(), MagicMock()]
            for c in clients:
                c.chat.completions.create.return_value = _make_response("ok")
            MockOpenAI.side_effect = clients

            llm = LLMClient(
                api_keys=["key1", "key2"],
                primary_model="m",
                fallback_models=[],
            )
            llm.chat([{"role": "user", "content": "a"}])
            llm.chat([{"role": "user", "content": "b"}])

        # Each client should have been called once (round-robin)
        clients[0].chat.completions.create.assert_called_once()
        clients[1].chat.completions.create.assert_called_once()

    def test_no_api_key_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key"):
                LLMClient(api_keys=[])
