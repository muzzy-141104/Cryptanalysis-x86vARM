# Requirements

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Ubuntu 20.04+ (or compatible Linux) | Ubuntu 22.04 LTS |
| Architecture | x86_64 or aarch64 | x86_64 (AMD/Intel) + aarch64 (Graviton2) |
| RAM | 4 GB | 8 GB+ |
| Disk | 10 GB free | 20 GB free |

## Core Build Tools

```bash
sudo apt update && sudo apt install -y \
  build-essential \
  gcc \
  g++ \
  cmake \
  make \
  git \
  pkg-config
```

## OpenSSL (libcrypto)

Required for all cryptographic drivers (`aes_driver`, `sha256_driver`, `chacha20_driver`).

```bash
sudo apt install -y libssl-dev
```

Verify:
```bash
pkg-config --modversion libcrypto
```

## Python 3 + Virtual Environment

```bash
sudo apt install -y python3 python3-venv python3-pip
```

Create and activate the project venv:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Python analysis dependencies:
```bash
pip install matplotlib pandas numpy
```

## Intel Pin (x86 Dynamic Binary Instrumentation)

Used for instruction-level profiling on x86.

1. Download Intel Pin from https://software.intel.com/content/www/us/en/developer/articles/tool/pin-a-dynamic-binary-instrumentation-tool.html
2. Extract and set environment:
```bash
export PIN_ROOT=/path/to/pin
export PATH=$PIN_ROOT:$PATH
```

3. Build the crypto profiler tool:
```bash
cd pin_tool
make -f makefile.rules
```

Set in your environment or pass to `run_all.sh`:
```bash
export PIN_BIN=$PIN_ROOT/pin
export PIN_TOOL_SO=pin_tool/obj-intel64/crypto_profiler.so
```

## DynamoRIO (x86 Dynamic Binary Instrumentation)

Alternative DBI backend for x86 profiling.

1. Download DynamoRIO from https://dynamorio.org/
2. Extract and set:
```bash
export DYNAMORIO_HOME=/path/to/DynamoRIO
```

3. Build the client (optional, pre-built `.so` is included):
```bash
cd dynamorio_client
mkdir build && cd build
cmake .. -DDynamoRIO_DIR=$DYNAMORIO_HOME/cmake
make
```

The pipeline uses `$DYNAMORIO_HOME/bin64/drrun` by default.

## Linux perf Subsystem

Used for hardware performance counter collection (x86 and ARM).

```bash
sudo apt install -y linux-tools-common linux-tools-$(uname -r)
```

Verify:
```bash
perf list
```

For ARM (Graviton), ensure `armv8_pmuv3_0` PMU events are available:
```bash
ls /sys/devices/armv8_pmuv3_0/events/
```

Note: On some cloud instances, PMU access is restricted by the hypervisor. Retired-instruction, branch, and cache counters may report `N/A`. Cycles and wall-clock throughput remain unaffected.

## Dashboard Backend (FastAPI)

```bash
cd dashboard/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Dependencies: `fastapi>=0.110`, `uvicorn[standard]>=0.27`

Run:
```bash
./run.sh
# or: uvicorn main:app --host 0.0.0.0 --port 8000
```

## Dashboard Frontend (React + Vite + Tailwind)

Requires Node.js 18+ and npm.

```bash
# Install Node.js (if not present)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

```bash
cd dashboard/frontend
npm install
```

Run in dev mode:
```bash
./run.sh
# or: npm run dev
```

Build for production (served by FastAPI):
```bash
BUILD=1 ./run.sh
# or: npm run build
```

## AWS Graviton2 Setup (ARM)

For ARM analysis on AWS Graviton2 instances, see `docs/aws_graviton_setup.md`.

Key steps:
1. Launch an `c6g.large` or larger Graviton2 instance (Ubuntu 22.04 AMI)
2. Install build tools and OpenSSL as above
3. Run the ARM environment setup script:
```bash
./scripts/setup_arm_env.sh
```

## Quick Start (x86)

```bash
# Install all system dependencies
sudo apt update && sudo apt install -y build-essential gcc cmake make git libssl-dev python3 python3-venv python3-pip

# Create Python venv and install packages
python3 -m venv .venv
source .venv/bin/activate
pip install matplotlib pandas numpy

# Build drivers
./scripts/build_arm_drivers.sh

# Run full pipeline (Pin + DynamoRIO + perf + charts + report)
./scripts/run_all.sh
```

## Quick Start (ARM / Graviton)

```bash
# Setup environment
./scripts/setup_arm_env.sh
./scripts/build_arm_drivers.sh

# Run ARM profiling
./scripts/run_arm_perf.sh

# Generate ARM summary and cross-arch comparison
.venv/bin/python scripts/generate_arm_phase8c.py
```

## Quick Start (Dashboard)

```bash
# Terminal 1: Backend
cd dashboard/backend && ./run.sh

# Terminal 2: Frontend (dev)
cd dashboard/frontend && ./run.sh

# Or build and serve from FastAPI
cd dashboard/frontend && BUILD=1 ./run.sh
cd ../backend && ./run.sh
# Open http://localhost:8000/
```
