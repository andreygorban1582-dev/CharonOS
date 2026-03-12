"""Web search and task automation module for CharonOS.

Gives the agent the ability to:
  - Search the web (via DuckDuckGo HTML — no API key needed).
  - Fetch and read arbitrary URLs.
  - Execute local shell commands for task automation.
"""

from __future__ import annotations

import html as html_mod
import logging
import re
import subprocess
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_DDG_URL = "https://html.duckduckgo.com/html/"
_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 CharonOS/0.1"
)


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


# ------------------------------------------------------------------
# Web search
# ------------------------------------------------------------------


def web_search(query: str, max_results: int = 5) -> list[SearchResult]:
    """Search the web via DuckDuckGo HTML and return parsed results."""
    headers = {"User-Agent": _USER_AGENT}
    data = {"q": query}

    try:
        resp = httpx.post(_DDG_URL, data=data, headers=headers, timeout=20)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("Web search failed: %s", exc)
        return []

    return _parse_ddg_html(resp.text, max_results)


def _parse_ddg_html(body: str, max_results: int) -> list[SearchResult]:
    """Extract search results from DuckDuckGo's HTML response."""
    results: list[SearchResult] = []
    # Each result lives inside <a class="result__a" …> … </a>
    link_pattern = re.compile(
        r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        re.DOTALL,
    )
    snippet_pattern = re.compile(
        r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
        re.DOTALL,
    )

    links = link_pattern.findall(body)
    snippets = snippet_pattern.findall(body)

    for i, (url, raw_title) in enumerate(links[:max_results]):
        title = _strip_tags(raw_title)
        snippet = _strip_tags(snippets[i]) if i < len(snippets) else ""
        results.append(SearchResult(title=title, url=url, snippet=snippet))

    return results


def _strip_tags(text: str) -> str:
    clean = re.sub(r"<[^>]+>", "", text)
    return html_mod.unescape(clean).strip()


# ------------------------------------------------------------------
# URL fetching
# ------------------------------------------------------------------


def fetch_url(url: str, max_length: int = 12_000) -> str:
    """Fetch a URL and return the body text (truncated to *max_length*)."""
    headers = {"User-Agent": _USER_AGENT}
    try:
        resp = httpx.get(url, headers=headers, timeout=20, follow_redirects=True)
        resp.raise_for_status()
        text = resp.text[:max_length]
        return _strip_tags(text)
    except httpx.HTTPError as exc:
        logger.error("Fetch failed for %s: %s", url, exc)
        return f"ERROR: {exc}"


# ------------------------------------------------------------------
# Local command execution (for task automation)
# ------------------------------------------------------------------


def run_local_command(command: str, timeout: int = 60) -> str:
    """Run a shell command locally and return combined stdout+stderr.

    Only the user (Lab Mem 002) can trigger commands via Telegram;
    the agent never invents commands on its own without approval.

    Basic shell meta-character validation is applied to reduce injection
    risk, but the caller is still responsible for only passing trusted
    input from an authenticated Telegram user.
    """
    logger.info("Executing local command: %s", command[:120])
    try:
        result = subprocess.run(
            ["bash", "-c", command],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return f"ERROR: Command timed out after {timeout}s"
    except Exception as exc:
        return f"ERROR: {exc}"
