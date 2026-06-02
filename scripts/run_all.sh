#!/usr/bin/env bash

# End-to-end automation: builds drivers, builds the DynamoRIO client,
# runs Pin, DynamoRIO, and perf profiling, aggregates results, generates
# charts/diagrams, and produces the report.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DATA_SIZE="${DATA_SIZE:-1048576}"
ITERATIONS="${ITERATIONS:-100}"
PYTHON_BIN="${PYTHON_BIN:-./.venv/bin/python}"
PIN_BIN="${PIN_BIN:-}"
PIN_TOOL_SO="${PIN_TOOL_SO:-}"
DYNAMORIO_HOME="${DYNAMORIO_HOME:-$HOME/tools/DynamoRIO}"
DYNAMORIO_BIN="${DYNAMORIO_BIN:-$DYNAMORIO_HOME/bin64/drrun}"

mkdir -p build results/x86 results/perf results/comparison logs/perf charts docs/diagrams

echo "=== [1/9] Build drivers ==="
gcc drivers/aes_driver.c      -O2 -o build/aes_driver      -lcrypto
gcc drivers/sha256_driver.c   -O2 -o build/sha256_driver   -lcrypto
gcc drivers/chacha20_driver.c -O2 -o build/chacha20_driver -lcrypto

echo "=== [2/9] Build DynamoRIO client ==="
if [[ -d "$DYNAMORIO_HOME" ]]; then
    gcc -shared -fPIC -O2 -DLINUX -DX86_64 -DUNIX \
        -I"$DYNAMORIO_HOME/include" -I"$DYNAMORIO_HOME/ext/include" \
        dynamorio_client/dr_crypto_profiler.c \
        -o dynamorio_client/libdr_crypto_profiler.so \
        -L"$DYNAMORIO_HOME/lib64/release" -L"$DYNAMORIO_HOME/ext/lib64/release" \
        -ldrmgr -ldynamorio -lpthread
else
    echo "Warning: DYNAMORIO_HOME not found at $DYNAMORIO_HOME; skipping DynamoRIO build"
fi

echo "=== [3/9] Run Pin profiling ==="
if [[ -n "$PIN_BIN" && -n "$PIN_TOOL_SO" && -x "$PIN_BIN" && -f "$PIN_TOOL_SO" ]]; then
    "$PIN_BIN" -t "$PIN_TOOL_SO" -o results/x86/aes_profile.csv     -- ./build/aes_driver     "$DATA_SIZE" "$ITERATIONS" || true
    "$PIN_BIN" -t "$PIN_TOOL_SO" -o results/x86/sha256_profile.csv  -- ./build/sha256_driver  "$DATA_SIZE" "$ITERATIONS" || true
    "$PIN_BIN" -t "$PIN_TOOL_SO" -o results/x86/chacha20_profile.csv -- ./build/chacha20_driver "$DATA_SIZE" "$ITERATIONS" || true
else
    echo "Warning: PIN_BIN or PIN_TOOL_SO not set; skipping Pin profiling"
fi

echo "=== [4/9] Run DynamoRIO profiling ==="
if [[ -x "$DYNAMORIO_BIN" && -f "dynamorio_client/libdr_crypto_profiler.so" ]]; then
    "$DYNAMORIO_BIN" -c dynamorio_client/libdr_crypto_profiler.so results/x86/dr_aes_profile.csv     -- ./build/aes_driver     "$DATA_SIZE" "$ITERATIONS" || true
    "$DYNAMORIO_BIN" -c dynamorio_client/libdr_crypto_profiler.so results/x86/dr_sha256_profile.csv  -- ./build/sha256_driver  "$DATA_SIZE" "$ITERATIONS" || true
    "$DYNAMORIO_BIN" -c dynamorio_client/libdr_crypto_profiler.so results/x86/dr_chacha20_profile.csv -- ./build/chacha20_driver "$DATA_SIZE" "$ITERATIONS" || true
else
    echo "Warning: DynamoRIO not configured; skipping DynamoRIO profiling"
fi

echo "=== [5/9] Run perf profiling ==="
./scripts/run_perf.sh

echo "=== [6/9] Aggregate results ==="
"$PYTHON_BIN" scripts/aggregate_results.py
"$PYTHON_BIN" scripts/compare_pin_dynamorio.py
"$PYTHON_BIN" scripts/compare_unified.py

echo "=== [7/9] Generate charts and diagrams ==="
"$PYTHON_BIN" scripts/generate_charts.py
"$PYTHON_BIN" scripts/generate_perf_charts.py
"$PYTHON_BIN" scripts/generate_diagrams.py

echo "=== [8/9] Generate report ==="
"$PYTHON_BIN" scripts/generate_report.py

echo "=== [9/9] Done ==="
echo "Outputs:"
echo "  - results/x86/summary.csv, results/x86/report.md"
echo "  - results/perf/perf_summary.csv"
echo "  - results/comparison/{pin_vs_dynamorio.csv,unified_comparison.csv}"
echo "  - charts/*.png"
echo "  - docs/diagrams/*.png, docs/diagrams/*.svg"
echo "  - docs/final_report.md"
