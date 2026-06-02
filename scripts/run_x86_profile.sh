#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PIN_BIN="${PIN_BIN:-}"
PIN_TOOL_SO="${PIN_TOOL_SO:-}"
DATA_SIZE="${DATA_SIZE:-1048576}"
ITERATIONS="${ITERATIONS:-100}"
PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"

if [[ -z "$PIN_BIN" ]]; then
    echo "Error: PIN_BIN is not set"
    echo "Example: PIN_BIN=~/pin/pin"
    exit 1
fi

if [[ -z "$PIN_TOOL_SO" ]]; then
    echo "Error: PIN_TOOL_SO is not set"
    echo "Example: PIN_TOOL_SO=~/pin/source/tools/MyPinTool/obj-intel64/crypto_profiler.so"
    exit 1
fi

if [[ ! -x "$PIN_BIN" ]]; then
    echo "Error: PIN_BIN is not executable: $PIN_BIN"
    exit 1
fi

if [[ ! -f "$PIN_TOOL_SO" ]]; then
    echo "Error: PIN_TOOL_SO not found: $PIN_TOOL_SO"
    exit 1
fi

if [[ ! -x "build/aes_driver" || ! -x "build/sha256_driver" || ! -x "build/chacha20_driver" ]]; then
    echo "Error: expected drivers in build/ are missing or not executable"
    echo "Expected: build/aes_driver, build/sha256_driver, build/chacha20_driver"
    exit 1
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "Error: Python runner not found or not executable: $PYTHON_BIN"
    echo "Set PYTHON_BIN=/path/to/python if needed"
    exit 1
fi

mkdir -p results/x86 charts

echo "[1/6] Profiling AES"
"$PIN_BIN" -t "$PIN_TOOL_SO" -o results/x86/aes_profile.csv -- ./build/aes_driver "$DATA_SIZE" "$ITERATIONS"

echo "[2/6] Profiling SHA256"
"$PIN_BIN" -t "$PIN_TOOL_SO" -o results/x86/sha256_profile.csv -- ./build/sha256_driver "$DATA_SIZE" "$ITERATIONS"

echo "[3/6] Profiling ChaCha20"
"$PIN_BIN" -t "$PIN_TOOL_SO" -o results/x86/chacha20_profile.csv -- ./build/chacha20_driver "$DATA_SIZE" "$ITERATIONS"

echo "[4/6] Aggregating summary"
"$PYTHON_BIN" scripts/aggregate_results.py

echo "[5/6] Generating charts"
"$PYTHON_BIN" scripts/generate_charts.py

echo "[6/6] Generating report"
"$PYTHON_BIN" scripts/generate_report.py

echo "Completed x86 profiling pipeline"
