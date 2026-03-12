"""OpenRouter integration for CharonOS.

Provides LLM chat completions through the OpenRouter API.  The model
used is selected dynamically based on the agent's current tier.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterClient:
    """Thin async-capable client for OpenRouter chat completions."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        default_model: str = "cognitivecomputations/dolphin-mistral:latest",
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
        """Send a chat completion request and return the assistant reply.

        Parameters
        ----------
        messages : list[dict]
            OpenAI-style message list ([{"role": …, "content": …}, …]).
        model : str, optional
            Override the default model for this request.
        """
        if not self.is_configured:
            raise RuntimeError("OpenRouter API key not configured")

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
            "HTTP-Referer": "https://github.com/CharonOS",
            "X-Title": "CharonOS",
        }

        url = f"{self.base_url}/chat/completions"
        logger.debug("OpenRouter request → %s  model=%s", url, chosen_model)

        resp = httpx.post(url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        data = resp.json()

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            logger.error("Unexpected OpenRouter response: %s", data)
            raise RuntimeError(f"Bad OpenRouter response: {data}") from exc

    def list_models(self) -> list[dict]:
        """Fetch the list of available models from OpenRouter."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        resp = httpx.get(f"{self.base_url}/models", headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json().get("data", [])
