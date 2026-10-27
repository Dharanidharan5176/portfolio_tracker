#!/usr/bin/env bash
# scripts/dev.sh - Local Development Runner for Unix-like shells
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Starting Local Portfolio Tracker (Local-First Mode)..."

mkdir -p "$ROOT_DIR/local-data/backups"
mkdir -p "$ROOT_DIR/local-data/imports"
mkdir -p "$ROOT_DIR/local-data/exports"
mkdir -p "$ROOT_DIR/local-data/cache"
mkdir -p "$ROOT_DIR/local-data/logs"

VENV_PYTHON="$ROOT_DIR/.venv/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
    VENV_PYTHON="$ROOT_DIR/.venv/Scripts/python.exe"
fi

if [ ! -f "$VENV_PYTHON" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$ROOT_DIR/.venv"
    "$ROOT_DIR/.venv/bin/pip" install -e "$ROOT_DIR/backend"
fi

echo "Starting Backend on http://127.0.0.1:8000..."
"$VENV_PYTHON" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

trap "kill $BACKEND_PID 2>/dev/null || true" EXIT

echo "Starting Frontend on http://127.0.0.1:5173..."
cd "$ROOT_DIR/frontend"
npm run dev
