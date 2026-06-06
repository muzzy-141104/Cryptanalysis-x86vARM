#!/usr/bin/env bash

# run_arm_perf.sh
# Collect perf hardware counters for the AES, SHA256, and ChaCha20 drivers
# on the host where this script runs (intended for ARM, but works on x86 too).

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DATA_SIZE="${DATA_SIZE:-1048576}"
ITERATIONS="${ITERATIONS:-100}"
PERF_OUT_DIR="${PERF_OUT_DIR:-results/arm}"
PERF_LOG_DIR="${PERF_LOG_DIR:-logs/perf_arm}"
PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}"

EVENTS=(
    "cpu_cycles"
    "inst_retired"
    "br_retired"
    "br_mis_pred_retired"
    "l1d_cache"
    "l1d_cache_refill"
    "l1i_cache"
    "l1i_cache_refill"
    "stall_frontend"
    "stall_backend"
)

mkdir -p "$PERF_OUT_DIR" "$PERF_LOG_DIR"

if [[ ! -x "./build/aes_driver" || ! -x "./build/sha256_driver" || ! -x "./build/chacha20_driver" ]]; then
    echo "Error: driver binaries missing. Run scripts/build_arm_drivers.sh first."
    exit 1
fi

if ! command -v perf >/dev/null 2>&1; then
    echo "Error: perf not installed. Run scripts/setup_arm_env.sh first."
    exit 1
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="$(command -v python3)"
    else
        echo "Error: Python interpreter not found (.venv/bin/python or python3)"
        exit 1
    fi
fi

current_paranoid="$(cat /proc/sys/kernel/perf_event_paranoid)"
if [[ "$current_paranoid" -ge 2 ]]; then
    echo "Error: perf_event_paranoid=$current_paranoid blocks hardware counters"
    echo "Run:  sudo sysctl -w kernel.perf_event_paranoid=1"
    exit 1
fi

run_perf() {
    local algorithm="$1"
    local driver="$2"
    local perf_csv="$PERF_OUT_DIR/${algorithm}_perf.csv"
    local perf_log="$PERF_LOG_DIR/${algorithm}_perf.log"

    echo "[arm perf] $algorithm -> $driver"
    perf stat \
        -e "$(IFS=,; echo "${EVENTS[*]}")" \
        -o "$perf_log" \
        "./build/$driver" "$DATA_SIZE" "$ITERATIONS" >/dev/null 2>&1 || true

    if [[ ! -s "$perf_log" ]]; then
        echo "Error: perf log missing or empty: $perf_log" >&2
        return 1
    fi

    "$PYTHON_BIN" "$ROOT_DIR/scripts/parse_perf_log.py" \
        "$PERF_OUT_DIR" "$algorithm" "$perf_log" "$perf_csv"
    echo "Wrote $perf_csv"
}

run_perf "aes" "aes_driver"
run_perf "sha256" "sha256_driver"
run_perf "chacha20" "chacha20_driver"

"$PYTHON_BIN" "$ROOT_DIR/scripts/parse_perf_csv.py" "$PERF_OUT_DIR"

echo "Completed ARM perf pipeline"
