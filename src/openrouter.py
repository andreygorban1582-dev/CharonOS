"""
OpenRouter API client.

Uses the OpenAI-compatible endpoint exposed by OpenRouter so any model
available on the platform can be swapped in via OPENROUTER_MODEL.
"""

from __future__ import annotations

import os
from typing import Any

from openai import AsyncOpenAI

_DEFAULT_MODEL = "mistralai/mistral-7b-instruct"


def _build_client() -> AsyncOpenAI:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    return AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": os.environ.get(
                "OPENROUTER_REFERER",
                "https://github.com/andreygorban1582-dev/CharonOS",
            ),
            "X-Title": "CharonOS AI Agent",
        },
    )


async def chat(
    messages: list[dict[str, Any]],
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """
    Send *messages* to OpenRouter and return the assistant's reply text.

    Parameters
    ----------
    messages:
        OpenAI-style message list, e.g.
        ``[{"role": "user", "content": "Hello"}]``.
    model:
        OpenRouter model identifier.  Falls back to the ``OPENROUTER_MODEL``
        environment variable, then to ``mistralai/mistral-7b-instruct``.
    temperature:
        Sampling temperature (0–2).
    max_tokens:
        Maximum number of tokens to generate.
    """
    client = _build_client()
    resolved_model = model or os.environ.get("OPENROUTER_MODEL", _DEFAULT_MODEL)

    response = await client.chat.completions.create(
        model=resolved_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""
