#!/usr/bin/env bash

# setup_arm_env.sh
# Prepare an Ubuntu ARM (aarch64) environment for the crypto-analysis project.
# Installs build tools, OpenSSL, Python, and perf.

set -euo pipefail

if [[ "$(uname -m)" != "aarch64" && "$(uname -m)" != "arm64" ]]; then
    echo "Warning: this script targets aarch64; detected $(uname -m)"
    echo "Continuing anyway; the package list is broadly applicable."
fi

if [[ $EUID -ne 0 ]]; then
    echo "Re-running with sudo..."
    exec sudo bash "$0" "$@"
fi

echo "=== Updating apt ==="
apt update
apt -y upgrade

echo "=== Installing build tools ==="
apt install -y build-essential gcc g++ make cmake

echo "=== Installing OpenSSL ==="
apt install -y libssl-dev openssl

echo "=== Installing Python ==="
apt install -y python3 python3-venv python3-pip

echo "=== Installing perf ==="
apt install -y linux-tools-generic linux-tools-common || true

echo "=== Configuring perf_event_paranoid ==="
if [[ -w /proc/sys/kernel/perf_event_paranoid ]]; then
    echo 1 > /proc/sys/kernel/perf_event_paranoid
    echo "perf_event_paranoid set to 1"
else
    sysctl -w kernel.perf_event_paranoid=1 || true
fi

echo "=== Verifying versions ==="
gcc --version | head -n 1
openssl version
python3 --version
if command -v perf >/dev/null 2>&1; then
    perf --version
else
    echo "Warning: perf not found in PATH after install"
fi

echo "=== Done. Next steps: ==="
echo "  1. ./scripts/build_arm_drivers.sh"
echo "  2. ./scripts/run_arm_perf.sh"
echo "  3. ./scripts/run_arm_dynamorio.sh"
