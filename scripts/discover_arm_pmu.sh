#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/results/arm"
OUT_FILE="$OUT_DIR/available_pmu_events.txt"

mkdir -p "$OUT_DIR"

if ! command -v perf >/dev/null 2>&1; then
    echo "Error: perf not found in PATH" >&2
    exit 1
fi

perf list | python3 -c '
import re
import sys

events = set()
candidate = None

for raw in sys.stdin:
    line = raw.rstrip("\n")
    stripped = line.strip()

    if not stripped:
        candidate = None
        continue

    if not line.startswith(" "):
        m = re.match(r"^([a-z0-9_\-]+):$", stripped)
        if m:
            candidate = None
            continue
        continue

    token = stripped.split()[0]

    if re.fullmatch(r"[a-z0-9_\-]+", token):
        candidate = token
        continue

    if "Unit: armv8_pmuv3_0" in stripped and candidate:
        events.add(candidate)

for name in sorted(events):
    print(name)
' > "$OUT_FILE"

count="$(wc -l < "$OUT_FILE")"
echo "Discovered $count ARM PMU events"
echo "Wrote $OUT_FILE"
