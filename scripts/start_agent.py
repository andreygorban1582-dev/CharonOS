#!/usr/bin/env python3
"""CharonOS entry point.

Launch the agent:
    python -m scripts.start_agent

Or, after ``pip install -e .``:
    charonos
"""

from __future__ import annotations

import sys


def main() -> None:
    from charonos.agent import CharonAgent

    agent = CharonAgent()
    agent.run()


if __name__ == "__main__":
    main()
