#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DATA_SIZE="${DATA_SIZE:-1048576}"
ITERATIONS="${ITERATIONS:-100}"
PERF_OUT_DIR="${PERF_OUT_DIR:-results/perf}"
PERF_LOG_DIR="${PERF_LOG_DIR:-logs/perf}"

EVENTS=(
    "cpu-cycles"
    "instructions"
    "branch-instructions"
    "branch-misses"
    "cache-references"
    "cache-misses"
    "stalled-cycles-frontend"
    "stalled-cycles-backend"
)

mkdir -p "$PERF_OUT_DIR" "$PERF_LOG_DIR"

if [[ ! -x "./build/aes_driver" || ! -x "./build/sha256_driver" || ! -x "./build/chacha20_driver" ]]; then
    echo "Error: expected driver binaries in build/"
    echo "Expected: build/aes_driver, build/sha256_driver, build/chacha20_driver"
    exit 1
fi

if ! command -v perf >/dev/null 2>&1; then
    echo "Error: perf not found in PATH"
    exit 1
fi

current_paranoid="$(cat /proc/sys/kernel/perf_event_paranoid)"
if [[ "$current_paranoid" -ge 2 ]]; then
    echo "Error: /proc/sys/kernel/perf_event_paranoid=$current_paranoid blocks hardware counters"
    echo "Run:  sudo sysctl -w kernel.perf_event_paranoid=1"
    exit 1
fi

run_perf() {
    local algorithm="$1"
    local driver="$2"
    local perf_csv="$PERF_OUT_DIR/${algorithm}_perf.csv"
    local perf_log="$PERF_LOG_DIR/${algorithm}_perf.log"

    echo "[perf] $algorithm -> $driver"
    perf stat \
        -e "$(IFS=,; echo "${EVENTS[*]}")" \
        -o "$perf_log" \
        "./build/$driver" "$DATA_SIZE" "$ITERATIONS" >/dev/null 2>&1 || true

    if [[ ! -s "$perf_log" ]]; then
        echo "Error: perf log missing or empty: $perf_log" >&2
        return 1
    fi

    # Convert the human-readable perf log into a machine-readable CSV
    # using the same parser that the rest of the pipeline consumes.
    "${ROOT_DIR}/.venv/bin/python" "${ROOT_DIR}/scripts/parse_perf_log.py" \
        "$PERF_OUT_DIR" "$algorithm" "$perf_log" "$perf_csv"

    if [[ ! -s "$perf_csv" ]]; then
        echo "Error: perf CSV missing or empty: $perf_csv" >&2
        return 1
    fi

    echo "Wrote $perf_csv"
}

run_perf "aes" "aes_driver"
run_perf "sha256" "sha256_driver"
run_perf "chacha20" "chacha20_driver"

# Build the unified perf summary and validate that we got real numbers.
"${ROOT_DIR}/.venv/bin/python" "${ROOT_DIR}/scripts/parse_perf_csv.py" "$PERF_OUT_DIR"

echo "Completed perf profiling pipeline"
