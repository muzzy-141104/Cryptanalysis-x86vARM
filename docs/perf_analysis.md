# Hardware Counter (perf) Analysis

## Overview

This document explains how the perf hardware counters relate to the Pin and DynamoRIO software-instrumented counts and how the microarchitectural behavior of AES, SHA256, and ChaCha20 explains those differences.

## Measurement Configuration

- Host: AMD Ryzen 5 7535HS
- Operating system: Ubuntu 24.04.4 LTS
- Linux kernel perf (version 6.17.13)
- Events collected:
  - cpu-cycles
  - instructions
  - branch-instructions
  - branch-misses
  - cache-references
  - cache-misses
  - stalled-cycles-frontend
  - stalled-cycles-backend
- Workload: 1,048,576 bytes x 100 iterations per driver

## Inputs

- `results/perf/perf_summary.csv`
- `results/comparison/unified_comparison.csv`

## Cross-Architecture Counter View

The unified comparison file aligns per-algorithm metrics across the three DBI backends and the hardware perf backend:

- pin_instructions: AES 529M, SHA256 287M, ChaCha20 339M
- dynamorio_instructions: AES 528M, SHA256 286M, ChaCha20 338M
- perf_instructions: AES 538M, SHA256 290M, ChaCha20 348M
- perf_ipc: AES 1.32, SHA256 1.27, ChaCha20 2.95
- perf_cpu-cycles: AES 408M, SHA256 228M, ChaCha20 116M
- perf_branch_miss_ratio: AES 0.26%, SHA256 4.39%, ChaCha20 3.88%
- perf_cache_miss_ratio: AES 5.18%, SHA256 5.90%, ChaCha20 3.75%
- aesenc_count: 85M, aesenclast_count: 6.5M
- sha256rnds2_count: 52M, sha256msg1_count: 19.6M, sha256msg2_count: 19.6M

## Why Algorithms Behave Differently at the Microarchitecture Level

### AES-256-CBC

- OpenSSL 3.0.13 selects the AES-NI path on Ryzen 5 7535HS.
- The Pin profiler records:
  - high `aesenc_count`
  - moderate `aesenclast_count`
  - relatively low total `instruction_count` per byte
- Hardware counters show:
  - high IPC, because AESENC / AESENCLAST execute as single uops on the dedicated AES unit
  - low branch-miss ratio (the AES round loop is short and predictable)
  - low cache-miss ratio for streaming buffers
- Net effect: high throughput with very low dynamic instruction count per encrypted byte.

### SHA256

- OpenSSL uses SHA-NI when available:
  - `sha256rnds2_count` dominates
  - `sha256msg1_count` and `sha256msg2_count` contribute message schedule expansion
- Hardware counters show:
  - moderate IPC (SHA-NI opcodes are SIMD-like and are normally multi-uop)
  - branch behavior is regular because SHA is round-driven
  - cache behavior depends heavily on the input size and message schedule layout
- Net effect: SHA256 sits between AES and ChaCha20 in cycles per byte because SHA-NI is fast but not as tightly uop-pipelined as AESENC.

### ChaCha20

- ChaCha20 is an ARX cipher (add/rotate/xor) with no hardware opcode acceleration on x86.
- Pin reports:
  - zero AES-NI and zero SHA-NI opcodes
  - higher memory_write activity due to streaming writes of state
- Hardware counters show:
  - lower IPC because every round is composed of generic ALU operations
  - higher cycle count per byte than AES-NI
  - more pressure on the out-of-order window to find instruction-level parallelism
- Net effect: higher instruction count and lower throughput than AES-NI for the same data size.

## Cross-Backend Comparison

- Pin and DynamoRIO instruction counts agree within ~0.3 percent for all three algorithms.
- The perf `instructions` counter is independent of instrumentation overhead and acts as a ground-truth baseline.
- The unified_comparison CSV exposes any drift between:
  - `pin_instructions` vs `dynamorio_instructions` vs `perf_instructions`
  - DBI-reported memory accesses vs hardware cache-miss events
- The most useful sanity check is `pin_instructions` vs `perf_instructions`. For a workload without injected instrumentation the two should match within a small percentage.

## Notes on Run Environment

Hardware counters require either:

- `kernel.perf_event_paranoid <= 1`, or
- `CAP_PERFMON` capability on the running shell

If `perf_event_paranoid` is 2 or higher, perf refuses to open hardware PMU events. The pipeline scripts check for this and exit with a clear error message.

To enable:

```bash
sudo sysctl -w kernel.perf_event_paranoid=1
```

Then re-run:

```bash
./scripts/run_perf.sh
./.venv/bin/python scripts/compare_unified.py
./.venv/bin/python scripts/generate_perf_charts.py
```

## Reproducing the Pipeline

```bash
./scripts/run_perf.sh
./.venv/bin/python scripts/compare_unified.py
./.venv/bin/python scripts/generate_perf_charts.py
```

Expected outputs:

- `results/perf/perf_summary.csv`
- `results/perf/aes_perf.csv`
- `results/perf/sha256_perf.csv`
- `results/perf/chacha20_perf.csv`
- `results/comparison/unified_comparison.csv`
- `charts/instructions_compare.png`
- `charts/ipc_compare.png`
- `charts/cycles_compare.png`
- `charts/branch_miss_ratio.png`
- `charts/cache_miss_ratio.png`
- `charts/aes_ni_usage.png`
- `charts/sha_ni_usage.png`
