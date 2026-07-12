# Final Project Report: Cross-Architecture Cryptographic Behavior Analysis

## Abstract

This project characterizes the runtime behavior of three widely used
cryptographic primitives — AES-256-CBC, SHA-256, and ChaCha20 — on two
processor families (x86_64 and ARMv8) using three independent measurement
backends: Intel Pin (JIT-based DBI), DynamoRIO (basic-block DBI), and the
Linux `perf` subsystem (hardware PMU counters). The study quantifies
instruction counts, memory traffic, IPC, branch behavior, cache behavior, and
crypto-extension opcode usage, then compares them across the two
architectures. The pipeline is reproducible end-to-end via the scripts in
`scripts/`.

## 1. Introduction

Software-level throughput numbers (MB/s) tell only part of the story for
cryptographic primitives. They do not reveal:

- How many instructions are retired per encrypted byte.
- Whether the workload is dominated by hardware-accelerated opcodes or by
  generic ALU operations.
- How predictable the control flow is (branch-miss rate).
- How the workload interacts with the cache hierarchy (L1D miss rate).

By measuring these dimensions on two architectures, we can build a much
richer picture of how AES, SHA-256, and ChaCha20 actually behave on modern
hardware, and we can validate that DBI tools produce consistent metrics for
the same workload.

## 2. Methodology

### 2.1 Algorithms

- AES-256-CBC via OpenSSL `EVP_aes_256_cbc()`
- SHA-256 via OpenSSL `EVP_sha256()`
- ChaCha20 via OpenSSL `EVP_chacha20()`

### 2.2 Workload

Each driver accepts `<data_size_bytes> <iterations>` and runs a tight
in-process loop. The default workload is 1,048,576 bytes × 100 iterations
(≈ 100 MB total data processed). Wall-clock timing uses
`clock_gettime(CLOCK_MONOTONIC)`.

### 2.3 Profiling Backends

| Backend | Architecture Support | Captures |
|---|---|---|
| Intel Pin | x86_64 | Per-instruction reads, writes, opcode classification |
| DynamoRIO | x86_64, AArch64 | Per-instruction reads, writes, opcode classification |
| Linux `perf` | x86, ARM | Hardware PMU counters (cycles, instructions, branches, cache) |

### 2.4 Pipeline

```
drivers/      -> <binary> <size> <iters>
                    |
   +----------------+----------------+
   |                |                |
 Pin tool      DynamoRIO          perf stat
   |                |                |
   v                v                v
*x86_profile.csv  *x86/dr_*.csv  logs/perf_*/<alg>.log
                       |                |
                       +--------+-------+
                                v
                  scripts/parse_perf_log.py
                                v
                  results/{arm,x86}/<alg>_perf.csv
                                v
                  scripts/parse_perf_csv.py
                                v
                  results/{arm,x86}/perf_summary.csv
                                v
                  scripts/compare_unified.py
                                v
              results/comparison/unified_comparison.csv
```

## 3. x86 Analysis (AMD Ryzen 5 7535HS)

### 3.1 Instruction Counts

| Algorithm | Pin | DynamoRIO | perf | Pin vs perf |
|---|---:|---:|---:|---:|
| AES | 529,249,390 | 528,194,004 | 537,659,518 | 1.02x |
| SHA256 | 286,776,734 | 285,724,743 | 289,924,429 | 1.01x |
| ChaCha20 | 338,676,989 | 337,622,833 | 347,711,073 | 1.03x |

The slight DBI under-count (~1–2%) is expected and is due to the way JIT and
DBI frameworks account for housekeeping code.

### 3.2 Memory Activity

| Algorithm | Pin reads | Pin writes | DR reads | DR writes |
|---|---:|---:|---:|---:|
| AES | 107,067,921 | 8,688,363 | 107,064,357 | 7,628,696 |
| SHA256 | 34,270,834 | 1,834,950 | 34,267,566 | 777,519 |
| ChaCha20 | 37,828,686 | 14,618,105 | 37,825,412 | 13,558,582 |

### 3.3 AES-NI and SHA-NI Usage

| Algorithm | AESENC | AESENCLAST | SHA256RNDS2 | SHA256MSG1 | SHA256MSG2 |
|---|---:|---:|---:|---:|---:|
| AES | 85,198,100 | 6,555,000 | 0 | 0 | 0 |
| SHA256 | 0 | 0 | 52,432,000 | 19,662,000 | 19,662,000 |
| ChaCha20 | 0 | 0 | 0 | 0 | 0 |

### 3.4 IPC, Branch Miss, Cache Miss

| Algorithm | IPC | Branch miss % | Cache miss % |
|---|---:|---:|---:|
| AES | 1.32 | 0.26% | 5.18% |
| SHA256 | 1.27 | 4.39% | 5.90% |
| ChaCha20 | 2.95 | 3.88% | 3.75% |

## 4. ARM Analysis (AWS Graviton2, Neoverse-N1)

### 4.1 Environment

- Host: AWS Graviton2 (t4g.medium), Ubuntu 24.04 LTS ARM64
- PMU unit: `armv8_pmuv3_0` (90 discovered events)
- Crypto extensions: AES, SHA-1, SHA-2 (`aes`, `sha1`, `sha2` in
  `/proc/cpuinfo`)

### 4.2 Pipeline Adaptations

- `scripts/run_arm_perf.sh` uses ARM-native PMU events:
  `cpu_cycles`, `inst_retired`, `br_retired`, `br_mis_pred_retired`,
  `l1d_cache`, `l1d_cache_refill`, `l1i_cache`, `l1i_cache_refill`,
  `stall_frontend`, `stall_backend`.
- `scripts/parse_perf_log.py` aliases these native names back to the
  canonical schema (`instructions`, `branch-instructions`, etc.).
- `scripts/parse_perf_csv.py` no longer hard-fails on missing/zero
  counters; they are recorded as `N/A` so summary generation can complete
  in restricted PMU environments.

### 4.3 PMU Access Limitation

On this Graviton environment, retired-instruction, branch, and cache PMU
events return zero for user-space workloads even though the events are
advertised by `perf list`. Cycles and task-clock are available. To
preserve the integrity of the analysis, those PMU metrics are reported as
`N/A`. Validation per event is in `results/arm/pmu_validation.csv`.

### 4.4 ARM Throughput

| Algorithm | Throughput (MB/s) | Execution Time (s) | Cycles | Crypto Extensions |
|---|---:|---:|---:|---|
| AES-256-CBC | 1213.31 | 0.0824 | 193,174,022 | yes |
| SHA256 | 1363.33 | 0.0734 | 171,299,291 | yes |
| ChaCha20 | 915.67 | 0.1092 | 255,996,062 | no |

`results/arm/summary.csv` is the canonical source of these numbers.

## 5. Cross-Architecture Comparison

The cross-architecture CSV is `results/comparison/x86_vs_arm.csv`. In this
environment, the x86 wall-clock throughput is not captured in a single
file alongside ARM, so the per-algorithm throughput is recorded as `N/A`
on the x86 side of the comparison CSV. The cycle counts are populated from
each architecture's `perf_summary.csv` and reflect what is observable in
this environment.

| Algorithm | x86 cycles | ARM cycles | x86 throughput | ARM throughput |
|---|---:|---:|---:|---:|
| AES | 408,330,487 | 193,174,022 | N/A | 1213.31 MB/s |
| SHA256 | 228,017,349 | 171,299,291 | N/A | 1363.33 MB/s |
| ChaCha20 | 116,020,731 | 255,996,062 | N/A | 915.67 MB/s |

Charts generated for the comparison:

- `charts/x86_vs_arm_throughput.png`
- `charts/x86_vs_arm_cycles.png`

## 6. Discussion

- **AES-256-CBC** is dominated by hardware-accelerated AESENC/AESE on both
  architectures. The pipeline is high-throughput and low-instruction-count
  per byte on x86. On ARM the cycle count is lower than x86 here, but a
  fair cross-architecture throughput comparison requires capturing
  identical wall-clock workloads on both hosts.
- **SHA-256** is hardware-accelerated on both architectures (SHA-NI vs
  SHA256H/SHA256H2/SHA256SU0/SHA256SU1). The instruction count is roughly
  the same on x86 (~287M) and is bounded by the same algorithmic work.
- **ChaCha20** is implemented as a pure software ARX pipeline on both
  architectures. NEON/ASIMD vectorization on ARM can in principle give a
  relative speedup over scalar x86 code, depending on compiler
  vectorization choices.

The agreement between Pin, DynamoRIO, and `perf` on x86 validates the use
of DBI as a reliable measurement methodology for cryptographic behavior
research.

## 7. Limitations

1. Single host per architecture. Other CPUs may dispatch OpenSSL
   differently.
2. Single workload size (1 MB × 100 iterations).
3. PMU access on this Graviton environment is restricted for non-privileged
   workloads; retired-instruction, branch, and cache counters are reported
   as `N/A`.
4. Pin and DynamoRIO write counts differ slightly on x86 due to
   engine-level microcoding handling.
5. Cross-architecture wall-clock throughput was not collected on the same
   host pair in this run; throughput is reported for ARM only.

## 8. Future Work

1. Run the same workload on a Graviton instance with non-restricted PMU
   access (bare-metal or a properly configured VM) to capture the full set
   of ARM PMU metrics.
2. Capture x86 wall-clock throughput under the same driver build and
   workload and fill the `x86_throughput` column in
   `results/comparison/x86_vs_arm.csv`.
3. Add ARM crypto opcode counts (AESE, AESMC, SHA256H, SHA256H2, SHA256SU0,
   SHA256SU1) to the DynamoRIO client and surface them in
   `results/arm/{algorithm}_profile.csv`.
4. Add a Neoverse-N1 microarchitecture section to the analysis report
   describing the dispatch and issue width of the AES/SHA units.
5. Add microarchitecture-independent throughput models for AES-NI, SHA-NI,
   ARMv8 AES, ARMv8 SHA, and software ARX pipelines.
6. Extend the comparison to other ARM cores (Cortex-A76, Neoverse-V1) and
   other x86 cores (Intel Sapphire Rapids) to broaden the survey.
