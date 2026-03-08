#!/usr/bin/env python3
"""
CharonOS AI Agent — entry point.

Usage
-----
Run the Telegram bot (default):
    python main.py

Run an interactive CLI session:
    python main.py --cli
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from dotenv import load_dotenv

load_dotenv()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CharonOS AI Agent")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Start an interactive CLI session instead of the Telegram bot",
    )
    return parser.parse_args()


async def _cli_loop() -> None:
    from src.agent import handle_message

    print("CharonOS AI — CLI mode. Type 'exit' or Ctrl-C to quit.\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        if not user_input:
            continue
        reply = await handle_message(user_input)
        print(f"\nAI: {reply}\n")


def main() -> None:
    args = _parse_args()

    if args.cli:
        asyncio.run(_cli_loop())
    else:
        from src.telegram_bot import run
        run()


if __name__ == "__main__":
    main()
