#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

if [[ ! -d ".venv" ]]; then
    python3 -m venv .venv
fi

.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

export PROJECT_ROOT="${PROJECT_ROOT:-$HERE/../..}"
export DASHBOARD_HOST="${DASHBOARD_HOST:-0.0.0.0}"
export DASHBOARD_PORT="${DASHBOARD_PORT:-8000}"

echo "Starting dashboard backend on http://${DASHBOARD_HOST}:${DASHBOARD_PORT}"
.venv/bin/python main.py
