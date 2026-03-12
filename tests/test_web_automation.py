"""Tests for charonos.integrations.web_automation."""

from charonos.integrations.web_automation import (
    _strip_tags,
    run_local_command,
    SearchResult,
)


def test_strip_tags():
    assert _strip_tags("<b>Hello</b> &amp; world") == "Hello & world"


def test_run_local_command_echo():
    out = run_local_command("echo hello")
    assert "hello" in out


def test_run_local_command_timeout():
    out = run_local_command("sleep 10", timeout=1)
    assert "ERROR" in out or "timed out" in out.lower()


def test_search_result_dataclass():
    r = SearchResult(title="T", url="http://x.com", snippet="S")
    assert r.title == "T"
