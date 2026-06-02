#!/usr/bin/env bash

# build_arm_drivers.sh
# Cross-compile-friendly build of the AES, SHA256, and ChaCha20 drivers.
# Designed to run on aarch64 Ubuntu (Oracle Cloud ARM) but also works on x86.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

BUILD_DIR="${BUILD_DIR:-$ROOT_DIR/build}"
mkdir -p "$BUILD_DIR"

CC="${CC:-gcc}"
CFLAGS="${CFLAGS:--O2 -Wall}"
LIBS="${LIBS:--lcrypto}"

build_one() {
    local name="$1"
    local source="$2"
    echo "[cc] $name"
    "$CC" $CFLAGS "$source" -o "$BUILD_DIR/$name" $LIBS
}

build_one aes_driver      drivers/aes_driver.c
build_one sha256_driver   drivers/sha256_driver.c
build_one chacha20_driver drivers/chacha20_driver.c

echo "Drivers built:"
ls -l "$BUILD_DIR"/aes_driver "$BUILD_DIR"/sha256_driver "$BUILD_DIR"/chacha20_driver

echo "Verify ELF target:"
file "$BUILD_DIR"/aes_driver
