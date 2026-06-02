#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v xdg-open >/dev/null 2>&1; then
    echo "Error: xdg-open is not available on this system"
    exit 1
fi

chart_files=(
    "charts/instruction_count.png"
    "charts/memory_reads.png"
    "charts/memory_writes.png"
    "charts/aes_opcode_usage.png"
    "charts/sha_opcode_usage.png"
)

missing=0
for file in "${chart_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "Missing chart: $file"
        missing=1
    fi
done

if [[ "$missing" -ne 0 ]]; then
    echo "Generate charts first: .venv/bin/python scripts/generate_charts.py"
    exit 1
fi

for file in "${chart_files[@]}"; do
    xdg-open "$file" >/dev/null 2>&1 &
done

echo "Opened chart images from charts/"
