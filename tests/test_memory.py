"""Tests for agent.memory (no git push, no real repo needed)."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from agent.memory import PersistentMemory


@pytest.fixture()
def mem(tmp_path):
    """Return a PersistentMemory instance backed by a temp directory."""
    with patch("agent.memory.git.Repo") as mock_repo_cls:
        # Make _commit_and_push a no-op
        mock_repo = MagicMock()
        mock_repo.is_dirty.return_value = False
        mock_repo_cls.return_value = mock_repo
        m = PersistentMemory(repo_path=str(tmp_path), commit_every=100)
    return m


class TestPersistentMemory:
    def test_add_and_get_history(self, mem):
        mem.add_message("user1", "user", "Hello")
        mem.add_message("user1", "assistant", "Hi there!")
        history = mem.get_history("user1")
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"

    def test_history_isolated_per_user(self, mem):
        mem.add_message("alice", "user", "Hi Alice here")
        mem.add_message("bob", "user", "Hi Bob here")
        assert len(mem.get_history("alice")) == 1
        assert len(mem.get_history("bob")) == 1

    def test_max_history_trimming(self, tmp_path):
        with patch("agent.memory.git.Repo"):
            m = PersistentMemory(repo_path=str(tmp_path), max_history_per_user=3, commit_every=100)
        for i in range(10):
            m.add_message("u", "user", f"msg {i}")
        assert len(m.get_history("u")) == 3
        assert m.get_history("u")[-1]["content"] == "msg 9"

    def test_facts(self, mem):
        mem.set_fact("language", "English")
        assert mem.get_fact("language") == "English"
        assert mem.get_fact("missing", "default") == "default"

    def test_clear_user(self, mem):
        mem.add_message("user1", "user", "test")
        with patch.object(mem, "_commit_and_push"):
            mem.clear_user("user1")
        assert mem.get_history("user1") == []

    def test_save_writes_json_files(self, mem):
        mem.add_message("u", "user", "persist me")
        with patch.object(mem, "_commit_and_push"):
            mem.save(commit=True)
        assert (mem.memory_dir / "conversations.json").exists()
        data = json.loads((mem.memory_dir / "conversations.json").read_text())
        assert "u" in data

    def test_load_persists_across_instances(self, tmp_path):
        with patch("agent.memory.git.Repo"):
            m1 = PersistentMemory(repo_path=str(tmp_path), commit_every=100)
            m1.add_message("u", "user", "remember this")
            with patch.object(m1, "_commit_and_push"):
                m1.save(commit=True)

        with patch("agent.memory.git.Repo"):
            m2 = PersistentMemory(repo_path=str(tmp_path), commit_every=100)
        history = m2.get_history("u")
        assert len(history) == 1
        assert history[0]["content"] == "remember this"
