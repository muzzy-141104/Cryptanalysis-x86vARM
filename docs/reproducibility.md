# Reproducibility Package

This document captures the exact environment, commands, and validation steps that produced the numbers in the final report.

## Host Machine

- CPU: AMD Ryzen 5 7535HS (AES-NI, SHA-NI, AVX2)
- Memory: 16 GB DDR5
- OS: Ubuntu 24.04.4 LTS
- Kernel: 6.17.0-35-generic

## Compiler and Libraries

- GCC 13.3 (Ubuntu 13.3.0-6ubuntu2~24.04.1)
- OpenSSL 3.0.13
- Intel Pin 4.2
- DynamoRIO (latest Linux x86_64 release)

## Environment Variables

```bash
export PIN_ROOT=$HOME/pin
export DYNAMORIO_HOME=$HOME/tools/DynamoRIO
export PATH=$DYNAMORIO_HOME/bin64:$PATH
```

## Linux Kernel Configuration

```bash
sudo sysctl -w kernel.perf_event_paranoid=1
```

Without this, hardware counters are blocked for non-privileged users.

## Build Commands

```bash
# Drivers
gcc drivers/aes_driver.c     -O2 -o build/aes_driver     -lcrypto
gcc drivers/sha256_driver.c  -O2 -o build/sha256_driver  -lcrypto
gcc drivers/chacha20_driver.c -O2 -o build/chacha20_driver -lcrypto

# Pin tool
# (use Pin's own make flow inside $PIN_ROOT/source/tools/MyPinTool)

# DynamoRIO client
gcc -shared -fPIC -O2 -DLINUX -DX86_64 -DUNIX \
  -I"$DYNAMORIO_HOME/include" -I"$DYNAMORIO_HOME/ext/include" \
  dynamorio_client/dr_crypto_profiler.c \
  -o dynamorio_client/libdr_crypto_profiler.so \
  -L"$DYNAMORIO_HOME/lib64/release" -L"$DYNAMORIO_HOME/ext/lib64/release" \
  -ldrmgr -ldynamorio -lpthread
```

## Run Commands

```bash
# Pin
"$PIN_ROOT/pin" -t "$PIN_TOOL_SO" -o results/x86/aes_profile.csv -- ./build/aes_driver 1048576 100
"$PIN_ROOT/pin" -t "$PIN_TOOL_SO" -o results/x86/sha256_profile.csv -- ./build/sha256_driver 1048576 100
"$PIN_ROOT/pin" -t "$PIN_TOOL_SO" -o results/x86/chacha20_profile.csv -- ./build/chacha20_driver 1048576 100

# DynamoRIO
"$DYNAMORIO_HOME/bin64/drrun" -c dynamorio_client/libdr_crypto_profiler.so \
  results/x86/dr_aes_profile.csv -- ./build/aes_driver 1048576 100
"$DYNAMORIO_HOME/bin64/drrun" -c dynamorio_client/libdr_crypto_profiler.so \
  results/x86/dr_sha256_profile.csv -- ./build/sha256_driver 1048576 100
"$DYNAMORIO_HOME/bin64/drrun" -c dynamorio_client/libdr_crypto_profiler.so \
  results/x86/dr_chacha20_profile.csv -- ./build/chacha20_driver 1048576 100

# perf
./scripts/run_perf.sh
```

## Aggregation Commands

```bash
./.venv/bin/python scripts/aggregate_results.py
./.venv/bin/python scripts/compare_pin_dynamorio.py
./.venv/bin/python scripts/compare_unified.py
./.venv/bin/python scripts/parse_perf_csv.py
```

## Visualization Commands

```bash
./.venv/bin/python scripts/generate_charts.py
./.venv/bin/python scripts/generate_perf_charts.py
./.venv/bin/python scripts/generate_diagrams.py
./.venv/bin/python scripts/generate_report.py
```

## One-Command Reproduction

```bash
./scripts/run_all.sh
```

## Validation Procedure

After the pipeline completes, verify the following invariants:

1. `results/perf/perf_summary.csv` contains non-zero `instructions` for all three algorithms.
2. Pin and DynamoRIO instruction counts differ by less than 0.4%:

   | Algorithm | Pin | DynamoRIO | Diff |
   |---|---:|---:|---:|
   | AES | 529,249,390 | 528,194,004 | 0.20% |
   | SHA256 | 286,776,734 | 285,724,743 | 0.37% |
   | ChaCha20 | 338,676,989 | 337,622,833 | 0.31% |

3. `perf` instructions are within 1-3% of Pin:

   | Algorithm | Pin | perf | Diff |
   |---|---:|---:|---:|
   | AES | 529,249,390 | 537,659,518 | 1.59% |
   | SHA256 | 286,776,734 | 289,924,429 | 1.10% |
   | ChaCha20 | 338,676,989 | 347,711,073 | 2.67% |

4. AES-CBC records non-zero `aesenc_count` and `aesenclast_count`.
5. SHA256 records non-zero `sha256rnds2_count`, `sha256msg1_count`, `sha256msg2_count`.
6. ChaCha20 records zero AES-NI and zero SHA-NI opcodes.

## Package Versions (Locked)

| Package | Version |
|---|---|
| Ubuntu | 24.04.4 LTS |
| Kernel | 6.17.0-35-generic |
| GCC | 13.3.0-6ubuntu2~24.04.1 |
| OpenSSL | 3.0.13 |
| Pin | 4.2 |
| DynamoRIO | latest Linux x86_64 release |
| pandas | 3.0.3 |
| matplotlib | 3.10.9 |
| numpy | 2.4.6 |
| python | 3.12.x |
