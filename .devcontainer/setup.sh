#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# CharonOS post-create setup for GitHub Codespaces
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Creating memory directory (if absent)..."
mkdir -p memory

echo "==> Copying .env template (if .env does not already exist)..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "    ✔ .env created — please fill in your API keys before running the bot."
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  CharonOS AI Agent — Codespace is ready!                ║"
echo "║                                                          ║"
echo "║  Next steps:                                             ║"
echo "║  1. Edit .env and add your API keys                      ║"
echo "║  2. Run:  python -m agent.main                           ║"
echo "╚══════════════════════════════════════════════════════════╝"
