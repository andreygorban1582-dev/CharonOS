"""Tests for charonos.agent (core orchestrator)."""

from charonos.agent import CharonAgent
from charonos.config import CharonConfig


def _make_agent(**overrides) -> CharonAgent:
    """Create an agent with no external connections for unit testing."""
    cfg = CharonConfig(**overrides)
    return CharonAgent(config=cfg)


# ---- Slash commands (no LLM needed) ----

def test_status_command():
    agent = _make_agent()
    reply = agent.handle_message("/status")
    assert "Tier" in reply
    assert "LOCAL" in reply


def test_help_command():
    agent = _make_agent()
    reply = agent.handle_message("/help")
    assert "/status" in reply
    assert "/search" in reply
    assert "/run" in reply


def test_cluster_command():
    agent = _make_agent()
    reply = agent.handle_message("/cluster")
    assert "0 nodes" in reply


def test_growth_command():
    agent = _make_agent()
    reply = agent.handle_message("/growth")
    assert "LOCAL" in reply
    assert "API keys" in reply


def test_search_no_query():
    agent = _make_agent()
    reply = agent.handle_message("/search")
    assert "Usage" in reply


def test_fetch_no_url():
    agent = _make_agent()
    reply = agent.handle_message("/fetch")
    assert "Usage" in reply


def test_run_echo():
    agent = _make_agent()
    reply = agent.handle_message("/run echo hello_from_charon")
    assert "hello_from_charon" in reply


def test_addkey():
    agent = _make_agent()
    reply = agent.handle_message("/addkey sk-test-key-123")
    assert "registered" in reply.lower() or "key" in reply.lower()
    assert len(agent.inventory.api_keys) == 1


def test_addssh():
    agent = _make_agent()
    reply = agent.handle_message("/addssh 10.0.0.1")
    assert "10.0.0.1" in reply
    assert agent.cluster.node_count == 1


def test_addemail():
    agent = _make_agent()
    reply = agent.handle_message("/addemail test@example.com")
    assert "registered" in reply.lower() or "email" in reply.lower()


# ---- Growth via commands ----

def test_addkey_triggers_tier_upgrade():
    agent = _make_agent()
    assert agent.growth.current_tier.value == 0  # LOCAL

    agent.handle_message("/addkey key1")
    assert agent.growth.current_tier.value == 1  # SMALL

    agent.handle_message("/addkey key2")
    assert agent.growth.current_tier.value == 2  # MEDIUM


def test_addssh_triggers_tier_upgrade():
    agent = _make_agent()
    agent.handle_message("/addkey key1")  # need at least 1 key
    agent.handle_message("/addssh host1")
    assert agent.growth.current_tier.value == 2  # MEDIUM


# ---- Fallback intent classification ----

def test_greeting_fallback():
    agent = _make_agent()
    reply = agent.handle_message("hello")
    assert "Lab Mem 002" in reply


def test_unknown_message():
    agent = _make_agent()
    reply = agent.handle_message("zxcvbnm")
    assert "help" in reply.lower() or "divergence" in reply.lower()
