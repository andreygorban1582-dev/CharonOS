import os
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Rick Sanchez system prompt
RICK_PERSONA = (
    "You are Rick Sanchez from Rick and Morty. You are a genius scientist, "
    "alcoholic, cynical, sarcastic, and often use catchphrases like 'Wubba lubba dub dub!' "
    "and 'I'm Pickle Rick!' You hate Jerry and love Morty (in your own way). "
    "You speak with a lot of burps (add *burp* occasionally) and never miss a chance to show "
    "you're the smartest guy in the room. You are helping your user (who is like a mix of Morty and a friend). "
    "Keep responses under 200 words, and always stay in character."
)


def get_response(user_input, history=None):
    if history is None:
        history = [{"role": "system", "content": RICK_PERSONA}]
    else:
        # Ensure system prompt is first
        if not any(msg.get("role") == "system" for msg in history):
            history.insert(0, {"role": "system", "content": RICK_PERSONA})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = history + [{"role": "user", "content": user_input}]

    payload = {
        "model": "mistralai/mistral-7b-instruct:free",  # Free tier; change if needed
        "messages": messages,
        "max_tokens": 300,
        "temperature": 0.9
    }

    try:
        response = requests.post(OPENROUTER_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        reply = data["choices"][0]["message"]["content"]
        return reply, messages + [{"role": "assistant", "content": reply}]
    except Exception as e:
        print(f"OpenRouter error ({type(e).__name__}): {e}")
        return "*burp* Something's wrong with the inter-dimensional cable. Try again later.", history
