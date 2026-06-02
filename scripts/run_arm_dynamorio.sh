#!/usr/bin/env bash

# run_arm_dynamorio.sh
# Run the DynamoRIO client against the AES, SHA256, and ChaCha20 drivers.
# Designed for ARM (aarch64); falls back to x86_64 if ARM client is absent.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DATA_SIZE="${DATA_SIZE:-1048576}"
ITERATIONS="${ITERATIONS:-100}"
DYNAMORIO_HOME="${DYNAMORIO_HOME:-$HOME/tools/DynamoRIO}"
DYNAMORIO_BIN="${DYNAMORIO_BIN:-$DYNAMORIO_HOME/bin64/drrun}"
CLIENT_SO="${CLIENT_SO:-$ROOT_DIR/dynamorio_client/libdr_crypto_profiler.so}"
OUT_DIR="${OUT_DIR:-results/arm}"
LOG_DIR="${LOG_DIR:-logs/dynamorio_arm}"

mkdir -p "$OUT_DIR" "$LOG_DIR"

if [[ ! -x "$DYNAMORIO_BIN" ]]; then
    echo "Error: drrun not found at $DYNAMORIO_BIN"
    echo "Set DYNAMORIO_BIN to the DynamoRIO aarch64 drrun binary."
    exit 1
fi

if [[ ! -f "$CLIENT_SO" ]]; then
    echo "Error: DynamoRIO client library missing: $CLIENT_SO"
    echo "Build it first (see docs/dynamorio_setup.md, use -DARM_64 for aarch64)."
    exit 1
fi

if [[ ! -x "./build/aes_driver" || ! -x "./build/sha256_driver" || ! -x "./build/chacha20_driver" ]]; then
    echo "Error: driver binaries missing. Run scripts/build_arm_drivers.sh first."
    exit 1
fi

run_dr() {
    local algorithm="$1"
    local driver="$2"
    local out_csv="$OUT_DIR/${algorithm}_profile.csv"
    local log_file="$LOG_DIR/${algorithm}.log"

    echo "[arm dr] $algorithm -> $driver"
    "$DYNAMORIO_BIN" -c "$CLIENT_SO" "$out_csv" -- \
        "./build/$driver" "$DATA_SIZE" "$ITERATIONS" \
        >"$log_file" 2>&1 || true

    if [[ ! -s "$out_csv" ]]; then
        echo "Error: DynamoRIO CSV missing or empty: $out_csv (see $log_file)" >&2
        return 1
    fi
    echo "Wrote $out_csv"
}

run_dr "aes"      "aes_driver"
run_dr "sha256"   "sha256_driver"
run_dr "chacha20" "chacha20_driver"

echo "Completed ARM DynamoRIO pipeline"
