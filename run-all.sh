#!/usr/bin/env bash
set -euo pipefail

if ! command -v gnome-terminal >/dev/null 2>&1; then
  echo "gnome-terminal is not installed."
  echo "Run backend and frontend in separate terminals."
  exit 1
fi

gnome-terminal -- bash -lc "cd backend && npm install && npm run dev; exec bash"
gnome-terminal -- bash -lc "cd frontend && npm install && npm run dev; exec bash"
