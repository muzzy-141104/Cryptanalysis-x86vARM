# Cross-Platform Cryptographic Behavior Analysis (x86 vs ARM)

Research-oriented framework that compares instruction-level and memory-level behavior of cryptographic algorithms using **Intel Pin**, **DynamoRIO**, and **Linux perf**. The current submission focuses on x86_64; ARM support is staged for the next phase.

## Features

- AES-256-CBC, SHA256, and ChaCha20 benchmark drivers built on OpenSSL EVP.
- Intel Pin profiler with AES-NI and SHA-NI opcode detection.
- DynamoRIO profiler with basic-block aggregation, matching Pin's CSV schema.
- Linux `perf` hardware-counter pipeline with derived IPC, branch-miss, and cache-miss metrics.
- Unified comparison pipeline that merges Pin, DynamoRIO, `perf`, and opcode counts.
- Matplotlib chart generation.
- Markdown report generator.
- End-to-end automation via `scripts/run_all.sh`.
- Architecture diagrams in both PNG and SVG.

## Repository Structure

```
crypto-analysis/
├── build/                  # Compiled driver binaries
├── charts/                 # Generated PNG charts
├── docs/
│   ├── diagrams/           # Architecture diagrams (PNG + SVG)
│   ├── dynamorio_plan.md
│   ├── dynamorio_setup.md
│   ├── dynamorio_validation.md
│   ├── final_report.md
│   ├── deliverables.md
│   ├── pin_vs_dynamorio.md
│   ├── perf_analysis.md
│   ├── reproducibility.md
│   ├── results_appendix.md
│   ├── arm_deployment_plan.md   (legacy; replaced by aws_graviton_setup.md)
│   ├── arm_metrics.md
│   ├── aws_graviton_setup.md
│   └── x86_vs_arm_design.md
├── drivers/                # AES, SHA256, ChaCha20 driver sources
├── dynamorio_client/       # DynamoRIO client source and built .so
├── logs/                   # Runtime logs (incl. perf captures)
├── pin_tool/               # Pin tool source
├── results/
│   ├── x86/                # Pin and DynamoRIO per-algorithm CSVs
│   ├── arm/                # Reserved for ARM phase
│   ├── perf/               # perf per-algorithm CSVs and summary
│   └── comparison/         # Unified CSVs
├── scripts/                # Automation and analysis scripts
├── .venv/                  # Python virtual environment
└── README.md
```

## Installation

### System packages (Ubuntu 24.04)

```bash
sudo apt update
sudo apt install -y build-essential gcc python3 python3-venv cmake
```

### Python environment

```bash
python3 -m venv .venv
.venv/bin/pip install pandas matplotlib
```

### Intel Pin 4.2

Download from the official Intel Pin release page, then set:

```bash
export PIN_ROOT=$HOME/pin
```

Build the Pin tool using Pin's own build system (the `pin_tool/makefile.rules` is shared with the Pin source tree). Typical workflow:

```bash
cd $PIN_ROOT/source/tools/MyPinTool
# place crypto_profiler.cpp from this repo's pin_tool/ here
make
```

The resulting `.so` is consumed by `scripts/run_x86_profile.sh` via `PIN_TOOL_SO`.

### DynamoRIO

```bash
export DYNAMORIO_HOME=$HOME/tools/DynamoRIO
export PATH=$DYNAMORIO_HOME/bin64:$PATH
```

For details, see `docs/dynamorio_setup.md`.

## Building Drivers

```bash
gcc drivers/aes_driver.c     -O2 -o build/aes_driver     -lcrypto
gcc drivers/sha256_driver.c  -O2 -o build/sha256_driver  -lcrypto
gcc drivers/chacha20_driver.c -O2 -o build/chacha20_driver -lcrypto
```

## Building Pin Tool

Use the Pin-provided build system for `crypto_profiler.cpp`. The `-o` knob in the tool controls the output CSV path.

## Building DynamoRIO Client

```bash
gcc -shared -fPIC -O2 -DLINUX -DX86_64 -DUNIX \
  -I"$DYNAMORIO_HOME/include" -I"$DYNAMORIO_HOME/ext/include" \
  dynamorio_client/dr_crypto_profiler.c \
  -o dynamorio_client/libdr_crypto_profiler.so \
  -L"$DYNAMORIO_HOME/lib64/release" -L"$DYNAMORIO_HOME/ext/lib64/release" \
  -ldrmgr -ldynamorio -lpthread
```

## Running Pin

```bash
"$PIN_ROOT/pin" -t "$PIN_TOOL_SO" -o results/x86/aes_profile.csv -- ./build/aes_driver 1048576 100
```

Or use the full automation:

```bash
PIN_BIN="$PIN_ROOT/pin" \
PIN_TOOL_SO="$PIN_ROOT/source/tools/MyPinTool/obj-intel64/crypto_profiler.so" \
PYTHON_BIN=./.venv/bin/python \
./scripts/run_x86_profile.sh
```

## Running DynamoRIO

```bash
"$DYNAMORIO_HOME/bin64/drrun" -c dynamorio_client/libdr_crypto_profiler.so \
  results/x86/dr_aes_profile.csv -- ./build/aes_driver 1048576 100
```

## Running perf

```bash
sudo sysctl -w kernel.perf_event_paranoid=1
./scripts/run_perf.sh
```

## Generating Charts

```bash
./.venv/bin/python scripts/aggregate_results.py
./.venv/bin/python scripts/generate_charts.py
./.venv/bin/python scripts/generate_perf_charts.py
./.venv/bin/python scripts/generate_diagrams.py
```

## Generating Report

```bash
./.venv/bin/python scripts/generate_report.py
```

## End-to-End

```bash
./scripts/run_all.sh
```

This single command:

1. Builds all drivers.
2. Builds the DynamoRIO client.
3. Runs Pin profiling for AES, SHA256, ChaCha20.
4. Runs DynamoRIO profiling for the same.
5. Runs `perf` for the same.
6. Aggregates the per-tool CSVs into the unified comparison.
7. Generates all charts and diagrams.
8. Generates the report and the validation document.

## x86 Pipeline

The x86 pipeline runs entirely on the local laptop. Outputs go to `results/x86/` and `results/perf/`.

```bash
# Drivers
gcc drivers/aes_driver.c      -O2 -o build/aes_driver      -lcrypto
gcc drivers/sha256_driver.c   -O2 -o build/sha256_driver   -lcrypto
gcc drivers/chacha20_driver.c -O2 -o build/chacha20_driver -lcrypto

# Pin (requires PIN_BIN, PIN_TOOL_SO)
PIN_BIN="$PIN_ROOT/pin" \
PIN_TOOL_SO="$PIN_ROOT/source/tools/MyPinTool/obj-intel64/crypto_profiler.so" \
PYTHON_BIN=./.venv/bin/python \
./scripts/run_x86_profile.sh

# DynamoRIO x86
gcc -shared -fPIC -O2 -DLINUX -DX86_64 -DUNIX \
  -I"$DYNAMORIO_HOME/include" -I"$DYNAMORIO_HOME/ext/include" \
  dynamorio_client/dr_crypto_profiler.c \
  -o dynamorio_client/libdr_crypto_profiler.so \
  -L"$DYNAMORIO_HOME/lib64/release" -L"$DYNAMORIO_HOME/ext/lib64/release" \
  -ldrmgr -ldynamorio -lpthread
"$DYNAMORIO_HOME/bin64/drrun" -c dynamorio_client/libdr_crypto_profiler.so \
  results/x86/dr_aes_profile.csv -- ./build/aes_driver 1048576 100

# perf x86
sudo sysctl -w kernel.perf_event_paranoid=1
./scripts/run_perf.sh
```

## ARM Pipeline

The ARM pipeline runs on an AWS Graviton instance. Outputs go to `results/arm/`. See `docs/aws_graviton_setup.md` for full provisioning details.

```bash
# Once on the Graviton instance
./scripts/setup_arm_env.sh
./scripts/build_arm_drivers.sh

# DynamoRIO aarch64
gcc -shared -fPIC -O2 -DLINUX -DARM_64 -DUNIX \
  -I"$DYNAMORIO_HOME/include" -I"$DYNAMORIO_HOME/ext/include" \
  dynamorio_client/dr_crypto_profiler.c \
  -o dynamorio_client/libdr_crypto_profiler.so \
  -L"$DYNAMORIO_HOME/lib64/release" -L"$DYNAMORIO_HOME/ext/lib64/release" \
  -ldrmgr -ldynamorio -lpthread

# perf arm
sudo sysctl -w kernel.perf_event_paranoid=1
./scripts/run_arm_perf.sh

# DynamoRIO arm
./scripts/run_arm_dynamorio.sh
```

## Cross-Architecture Comparison Pipeline

After both x86 and ARM profiling runs are complete, merge the results into the unified comparison and fill in the cross-architecture tables.

```bash
# Build a single CSV that includes both x86 and ARM rows
./.venv/bin/python scripts/compare_unified.py

# Generate cross-architecture charts (where applicable)
./.venv/bin/python scripts/generate_perf_charts.py

# Manually fill docs/x86_vs_arm_design.md TBD rows with measured values
# then publish docs/x86_vs_arm_report.md as the final cross-architecture report
```

The cross-architecture diagram is at `docs/diagrams/cross_architecture_pipeline.png` (and `.svg`).

```text
Laptop (x86)
      |
      | SSH
      |
AWS Graviton ARM
      |
      ├── perf
      ├── DynamoRIO
      └── crypto-analysis
```

## Expected Outputs

- `results/x86/{aes,sha256,chacha20}_profile.csv`
- `results/x86/dr_{aes,sha256,chacha20}_profile.csv`
- `results/x86/summary.csv`, `results/x86/report.md`
- `results/perf/{aes,sha256,chacha20}_perf.csv`, `results/perf/perf_summary.csv`
- `results/arm/{aes,sha256,chacha20}_profile.csv` (after ARM run)
- `results/arm/{aes,sha256,chacha20}_perf.csv`
- `results/arm/perf_summary.csv`
- `results/comparison/pin_vs_dynamorio.csv`, `results/comparison/unified_comparison.csv`
- `charts/*.png`
- `docs/diagrams/*.png` and `*.svg` (including `cross_architecture_pipeline`)
- `docs/final_report.md`, `docs/results_appendix.md`, `docs/reproducibility.md`
- `docs/aws_graviton_setup.md`, `docs/x86_vs_arm_design.md`

## Troubleshooting

- **Hardware counters are blocked**: `sudo sysctl -w kernel.perf_event_paranoid=1`.
- **`drrun: cannot locate client library`**: confirm `DYNAMORIO_HOME` and that the client `.so` is built.
- **Pin tool crashes with XED errors**: ensure the tool is built against the same Pin kit as the runtime.
- **Zero counters in `perf_summary.csv`**: the pipeline now refuses to write zeros; rerun `scripts/run_perf.sh` with permissions to read PMU events.
- **Pin/DynamoRIO write counts disagree slightly**: this is a known engine-level difference for microcoded memory writes; see `docs/dynamorio_validation.md`.

See `docs/reproducibility.md` for the exact environment used to produce the reported numbers.
