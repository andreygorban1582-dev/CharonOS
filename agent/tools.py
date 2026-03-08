"""
Built-in tools available to the CharonOS agent.

Each tool is a plain callable that accepts keyword arguments and returns a
string result.  The registry maps tool names to callables so the agent can
look them up by name.
"""

from __future__ import annotations

import logging
import math
import re
from collections.abc import Callable

logger = logging.getLogger(__name__)


# ─── Individual tools ────────────────────────────────────────────────────────

def calculator(expression: str, **_) -> str:
    """
    Evaluate a safe mathematical expression and return the result.

    Supports basic arithmetic, exponentiation, and common math functions
    (sqrt, sin, cos, tan, log, abs, round, pi, e).
    """
    # Strip whitespace
    expr = expression.strip()

    # Allowlist of names available during eval
    safe_names: dict = {
        "__builtins__": {},
        "abs": abs,
        "round": round,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log2": math.log2,
        "log10": math.log10,
        "exp": math.exp,
        "pi": math.pi,
        "e": math.e,
        "pow": math.pow,
        "floor": math.floor,
        "ceil": math.ceil,
    }

    # Disallow any characters outside the set needed for math
    if not re.match(r"^[\d\s\+\-\*\/\(\)\.\^%,_a-zA-Z]+$", expr):
        return "Error: expression contains disallowed characters."

    try:
        result = eval(expr, safe_names)  # noqa: S307 (controlled safe_names)
        return str(result)
    except ZeroDivisionError:
        return "Error: division by zero."
    except Exception as exc:
        return f"Error: {exc}"


def word_count(text: str, **_) -> str:
    """Return the word and character count of the provided text."""
    words = len(text.split())
    chars = len(text)
    return f"Words: {words}, Characters: {chars}"


def help_tool(**_) -> str:
    """List all available tools."""
    lines = ["Available tools:"]
    for name, fn in REGISTRY.items():
        doc = (fn.__doc__ or "").strip().splitlines()[0]
        lines.append(f"  • {name}: {doc}")
    return "\n".join(lines)


# ─── Registry ────────────────────────────────────────────────────────────────

REGISTRY: dict[str, Callable] = {
    "calculator": calculator,
    "word_count": word_count,
    "help": help_tool,
}


def run_tool(name: str, **kwargs: object) -> str:
    """Execute a tool by name and return its string output."""
    tool = REGISTRY.get(name)
    if tool is None:
        available = ", ".join(REGISTRY.keys())
        return f"Unknown tool '{name}'. Available: {available}"
    try:
        return tool(**kwargs)
    except Exception as exc:
        logger.exception("Tool '%s' raised an exception", name)
        return f"Tool error: {exc}"
