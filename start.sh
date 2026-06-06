#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

BACKEND_PID=""
FRONTEND_PID=""
CLEANED_UP=0

cleanup() {
  if [[ "$CLEANED_UP" -eq 1 ]]; then
    return
  fi
  CLEANED_UP=1

  echo
  echo "Stopping Paper Insight..."
  if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID"
  fi
  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID"
  fi
}

trap cleanup EXIT INT TERM

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install it with: brew install uv"
  exit 1
fi

echo "Installing backend dependencies with uv..."
(
  cd "$BACKEND_DIR"
  uv sync --extra dev
)

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "Installing frontend dependencies..."
  npm --prefix "$FRONTEND_DIR" install
fi

echo "Starting backend: http://127.0.0.1:8000"
(
  cd "$BACKEND_DIR"
  uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
) &
BACKEND_PID=$!

echo "Starting frontend: http://127.0.0.1:5173"
npm --prefix "$FRONTEND_DIR" run dev &
FRONTEND_PID=$!

echo
echo "Paper Insight is starting."
echo "Open http://127.0.0.1:5173"
echo "Press Ctrl-C to stop both services."

wait "$BACKEND_PID" "$FRONTEND_PID"
