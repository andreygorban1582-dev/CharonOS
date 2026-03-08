"""
LLM client for CharonOS using OpenRouter.

Supports:
  - Multiple OpenRouter API keys (round-robin load balancing / failover)
  - Configurable primary model (default: Dolphin Mistral via OpenRouter)
  - Automatic fallback through a ranked list of models
"""

from __future__ import annotations

import itertools
import logging
import os
from typing import Iterator

from openai import OpenAI, APIError, RateLimitError, APIConnectionError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_DEFAULT_PRIMARY_MODEL = "cognitivecomputations/dolphin-mistral-24gb"
_DEFAULT_FALLBACKS = [
    "mistralai/mistral-7b-instruct",
    "nousresearch/nous-hermes-2-mixtral-8x7b-dpo",
    "meta-llama/llama-3.1-8b-instruct:free",
]

_RETRYABLE = (RateLimitError, APIConnectionError)


def _build_clients(api_keys: list[str]) -> list[OpenAI]:
    """Create one OpenAI client per API key."""
    return [
        OpenAI(base_url=OPENROUTER_BASE_URL, api_key=key)
        for key in api_keys
    ]


class LLMClient:
    """OpenRouter-backed LLM client with multi-key and multi-model support."""

    def __init__(
        self,
        api_keys: list[str] | None = None,
        primary_model: str | None = None,
        fallback_models: list[str] | None = None,
    ) -> None:
        # Gather API keys from argument or environment
        if not api_keys:
            primary_key = os.getenv("OPENROUTER_API_KEY", "")
            extra_keys = [
                k.strip()
                for k in os.getenv("OPENROUTER_EXTRA_KEYS", "").split(",")
                if k.strip()
            ]
            api_keys = [k for k in [primary_key] + extra_keys if k]

        if not api_keys:
            raise ValueError(
                "At least one OpenRouter API key must be supplied via "
                "OPENROUTER_API_KEY or the api_keys argument."
            )

        self._clients: list[OpenAI] = _build_clients(api_keys)
        # Cycle through clients for round-robin load balancing
        self._client_cycle: Iterator[OpenAI] = itertools.cycle(self._clients)

        self.primary_model: str = (
            primary_model
            or os.getenv("PRIMARY_MODEL", _DEFAULT_PRIMARY_MODEL)
        )

        raw_fallbacks = (
            fallback_models
            or [
                m.strip()
                for m in os.getenv(
                    "FALLBACK_MODELS", ",".join(_DEFAULT_FALLBACKS)
                ).split(",")
                if m.strip()
            ]
        )
        # Deduplicate while preserving order; primary must not appear in fallbacks
        seen: set[str] = {self.primary_model}
        self.fallback_models: list[str] = [
            m for m in raw_fallbacks if m not in seen and not seen.add(m)  # type: ignore[func-returns-value]
        ]

        self._extra_headers = {
            "HTTP-Referer": "https://github.com/andreygorban1582-dev/CharonOS",
            "X-Title": "CharonOS AI Agent",
        }

        logger.info(
            "LLMClient ready | primary=%s | fallbacks=%s | keys=%d",
            self.primary_model,
            self.fallback_models,
            len(self._clients),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        **kwargs,
    ) -> str:
        """
        Send a chat request and return the assistant reply as a string.

        Tries the requested model (or primary) first, then falls back through
        the fallback list.  Each attempt is itself retried on transient errors.
        """
        models_to_try = [model or self.primary_model] + self.fallback_models
        last_exc: Exception | None = None

        for attempt_model in models_to_try:
            client = next(self._client_cycle)
            try:
                return self._chat_with_retry(client, attempt_model, messages, **kwargs)
            except Exception as exc:
                logger.warning(
                    "Model %s failed (%s); trying next...", attempt_model, exc
                )
                last_exc = exc

        raise RuntimeError(
            f"All models failed. Last error: {last_exc}"
        ) from last_exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @retry(
        retry=retry_if_exception_type(_RETRYABLE),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
        reraise=True,
    )
    def _chat_with_retry(
        self,
        client: OpenAI,
        model: str,
        messages: list[dict],
        **kwargs,
    ) -> str:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            extra_headers=self._extra_headers,
            **kwargs,
        )
        content = response.choices[0].message.content
        if content is None:
            raise APIError(
                f"Empty response from model '{model}'", request=None, body=None
            )
        return content
