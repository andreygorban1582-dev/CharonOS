"""DeepSeek API integration for CharonOS.

Supports DeepSeek via its REST API (compatible with OpenAI format).
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.deepseek.com"


class DeepSeekClient:
    """Client for the DeepSeek chat completions API."""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = DEFAULT_BASE_URL,
        default_model: str = "deepseek-chat",
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def chat(
        self,
        messages: list[dict],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Send a chat-completion request and return the reply."""
        if not self.is_configured:
            raise RuntimeError("DeepSeek API key not configured")

        chosen_model = model or self.default_model

        payload = {
            "model": chosen_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/chat/completions"
        logger.debug("DeepSeek request → %s  model=%s", url, chosen_model)

        resp = httpx.post(url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            logger.error("Unexpected DeepSeek response: %s", data)
            raise RuntimeError(f"Bad DeepSeek response: {data}") from exc
