"""Tests for charonos.personality.okabe."""

from charonos.personality.okabe import (
    PersonalityTraits,
    SYSTEM_PROMPT,
    format_greeting,
    format_status_message,
    format_error_message,
    get_system_prompt,
)


def test_personality_traits_defaults():
    traits = PersonalityTraits()
    assert traits.name == "Hououin Kyouma"
    assert "El Psy Kongroo" in traits.catchphrase


def test_system_prompt_contains_key_phrases():
    prompt = get_system_prompt()
    assert "Hououin Kyouma" in prompt
    assert "Lab Member 001" in prompt
    assert "El Psy Kongroo" in prompt
    assert "Dolphin Mistral" in prompt


def test_format_greeting():
    msg = format_greeting()
    assert "CharonOS" in msg
    assert "Future Gadget Laboratory" in msg
    assert "Lab Member 002" in msg


def test_format_status_message():
    msg = format_status_message("All systems nominal")
    assert "All systems nominal" in msg
    assert "El Psy Kongroo" in msg


def test_format_status_no_sign_off():
    msg = format_status_message("test", sign_off=False)
    assert "El Psy Kongroo" not in msg


def test_format_error_message():
    msg = format_error_message("Disk full")
    assert "Organization" in msg
    assert "Disk full" in msg
