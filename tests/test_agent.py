"""
Tests for the agent slash-command handling (no LLM calls needed).
"""

from __future__ import annotations

import importlib
import pytest


@pytest.fixture(autouse=True)
def isolated_memory(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMORY_DIR", str(tmp_path))
    import src.memory as mem_mod
    importlib.reload(mem_mod)
    import src.agent as agent_mod
    importlib.reload(agent_mod)
    yield agent_mod
    importlib.reload(mem_mod)
    importlib.reload(agent_mod)


@pytest.mark.asyncio
async def test_help_command(isolated_memory):
    reply = await isolated_memory.handle_message("/help")
    assert "/clear" in reply
    assert "/remember" in reply


@pytest.mark.asyncio
async def test_clear_command(isolated_memory):
    import src.memory as mem
    mem.append_message("user", "hello")
    reply = await isolated_memory.handle_message("/clear")
    assert "cleared" in reply.lower()
    assert mem.load_history() == []


@pytest.mark.asyncio
async def test_remember_command(isolated_memory):
    import src.memory as mem
    reply = await isolated_memory.handle_message("/remember language=Python")
    assert "language" in reply
    assert mem.get_fact("language") == "Python"


@pytest.mark.asyncio
async def test_remember_bad_format(isolated_memory):
    reply = await isolated_memory.handle_message("/remember bad_input")
    assert "Usage" in reply


@pytest.mark.asyncio
async def test_facts_command_empty(isolated_memory):
    reply = await isolated_memory.handle_message("/facts")
    assert "No facts" in reply


@pytest.mark.asyncio
async def test_facts_command_with_data(isolated_memory):
    import src.memory as mem
    mem.save_fact("color", "blue")
    reply = await isolated_memory.handle_message("/facts")
    assert "color" in reply
    assert "blue" in reply
