"""Tests for charonos.context.rolling_context."""

import json
import tempfile
from pathlib import Path

from charonos.context.rolling_context import RollingContext, Message


def test_add_and_retrieve():
    ctx = RollingContext(max_tokens=10_000)
    ctx.add("user", "Hello")
    ctx.add("assistant", "Hi there")

    messages = ctx.get_context()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["content"] == "Hi there"


def test_system_prompt_prepended():
    ctx = RollingContext()
    ctx.add("user", "test")
    msgs = ctx.get_context(system_prompt="You are a bot.")
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"] == "You are a bot."


def test_compaction_when_over_budget():
    # Very small budget forces compaction
    ctx = RollingContext(max_tokens=10, chars_per_token=1)
    for i in range(20):
        ctx.add("user", f"message number {i} " * 3)

    # Some messages should have been compacted
    assert ctx.active_message_count < 20
    assert ctx.total_messages_ever == 20
    assert ctx.summary  # summary should be non-empty


def test_summary_included_in_context():
    ctx = RollingContext(max_tokens=10, chars_per_token=1)
    for i in range(20):
        ctx.add("user", f"msg {i} padding text here")

    msgs = ctx.get_context(system_prompt="sys")
    roles = [m["role"] for m in msgs]
    # system prompt + summary + active messages
    assert roles[0] == "system"
    assert roles[1] == "system"  # summary
    assert "Compacted" in msgs[1]["content"]


def test_persistence_round_trip():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = str(Path(tmpdir) / "ctx.json")
        ctx = RollingContext(persist_path=path)
        ctx.add("user", "hello")
        ctx.add("assistant", "world")
        ctx.save()

        ctx2 = RollingContext(persist_path=path)
        assert ctx2.active_message_count == 2
        assert ctx2.total_messages_ever == 2


def test_message_to_dict():
    m = Message(role="user", content="hi")
    d = m.to_dict()
    assert d == {"role": "user", "content": "hi"}
