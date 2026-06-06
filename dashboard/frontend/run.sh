#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

if [[ ! -d "node_modules" ]]; then
    npm install
fi

if [[ "${BUILD:-0}" == "1" ]]; then
    npm run build
    echo "Built frontend into $(pwd)/dist"
    exit 0
fi

if [[ -f "dist/index.html" ]]; then
    echo "Found built frontend. Serving via 'npm run preview' on http://localhost:5173"
    npm run preview -- --port 5173 --strictPort
else
    echo "Starting Vite dev server on http://localhost:5173"
    npm run dev -- --port 5173 --strictPort
fi
