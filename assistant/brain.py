import os

import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def get_response(user_input, history=None):
    """Send user input to OpenRouter and return the AI reply.

    Args:
        user_input: The message from the user.
        history: A list of previous message dicts (optional).

    Returns:
        A tuple of (reply_text, updated_history).
    """
    if history is None:
        history = []

    if not OPENROUTER_API_KEY:
        return "OpenRouter API key is not configured.", history

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    messages = history + [{"role": "user", "content": user_input}]

    payload = {
        "model": "mistralai/mistral-7b-instruct:free",
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.7,
    }

    try:
        response = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        return reply, messages + [{"role": "assistant", "content": reply}]
    except Exception as e:
        print(f"OpenRouter error: {e}")
        return "Sorry, I'm having trouble connecting to my brain.", history
