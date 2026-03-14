"""Miscellaneous helper functions for the AI assistant."""

import datetime


def timestamp():
    """Return a formatted UTC timestamp string."""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def is_urgent(text: str) -> bool:
    """Return True if the text contains an urgency keyword."""
    keywords = ["urgent", "emergency", "help", "alert"]
    return any(kw in text.lower() for kw in keywords)
