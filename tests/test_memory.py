"""
Tests for the persistent memory module.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_memory(tmp_path, monkeypatch):
    """Redirect MEMORY_DIR to a temporary directory for each test."""
    monkeypatch.setenv("MEMORY_DIR", str(tmp_path))
    # Force the module to re-read the env var by reloading it.
    import importlib
    import src.memory as mem_mod
    importlib.reload(mem_mod)
    yield mem_mod
    importlib.reload(mem_mod)  # restore defaults after test


def test_history_starts_empty(isolated_memory):
    assert isolated_memory.load_history() == []


def test_append_and_load_history(isolated_memory):
    isolated_memory.append_message("user", "hello")
    isolated_memory.append_message("assistant", "hi there")
    history = isolated_memory.load_history()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "hello"
    assert history[1]["role"] == "assistant"


def test_clear_history(isolated_memory):
    isolated_memory.append_message("user", "test")
    isolated_memory.clear_history()
    assert isolated_memory.load_history() == []


def test_save_and_get_fact(isolated_memory):
    isolated_memory.save_fact("name", "Alice")
    assert isolated_memory.get_fact("name") == "Alice"


def test_get_missing_fact_returns_default(isolated_memory):
    assert isolated_memory.get_fact("nonexistent", "default_val") == "default_val"


def test_facts_as_text(isolated_memory):
    isolated_memory.save_fact("city", "Berlin")
    text = isolated_memory.facts_as_text()
    assert "city" in text
    assert "Berlin" in text


def test_facts_as_text_empty(isolated_memory):
    assert isolated_memory.facts_as_text() == ""


def test_history_trim(isolated_memory, monkeypatch):
    monkeypatch.setenv("MAX_HISTORY_TURNS", "2")
    import importlib
    import src.memory as mem_mod
    importlib.reload(mem_mod)

    for i in range(10):
        mem_mod.append_message("user", f"msg {i}")

    history = mem_mod.load_history()
    # At most MAX_HISTORY_TURNS * 2 = 4 messages should be kept
    assert len(history) <= 4
