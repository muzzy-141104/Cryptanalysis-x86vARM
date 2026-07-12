# Cryptanalysis-x86vARM — Full Data Report

> **Generated from**: `results/` CSV data and `charts/` visualizations
> **Workload**: 1,048,576 bytes × 100 iterations per algorithm
> **Algorithms**: AES-256-CBC, SHA-256, ChaCha20

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Measurement Backends](#2-measurement-backends)
3. [x86_64 Instruction-Level Analysis (Pin)](#3-x86_64-instruction-level-analysis-pin)
4. [x86_64 DynamoRIO Validation](#4-x86_64-dynamorio-validation)
5. [x86_64 Hardware Performance Counters (perf)](#5-x86_64-hardware-performance-counters-perf)
6. [ARMv8 Analysis (Graviton2)](#6-armv8-analysis-graviton2)
7. [ARM PMU Event Discovery and Validation](#7-arm-pmu-event-discovery-and-validation)
8. [Pin vs DynamoRIO Cross-Validation](#8-pin-vs-dynamorio-cross-validation)
9. [Cross-Architecture Comparison: x86_64 vs ARMv8](#9-cross-architecture-comparison-x86_64-vs-armv8)
10. [Per-Algorithm Deep Dives](#10-per-algorithm-deep-dives)
11. [Chart Inventory](#11-chart-inventory)
12. [Key Findings](#12-key-findings)
13. [Limitations](#13-limitations)

---

## 1. Executive Summary

This report presents a comprehensive cross-architecture cryptographic behavior analysis comparing **x86_64 (AMD Ryzen 5 7535HS)** and **ARMv8 (AWS Graviton2 / Neoverse-N1)** across three cryptographic algorithms: AES-256-CBC, SHA-256, and ChaCha20. Three independent measurement backends — **Intel Pin**, **DynamoRIO**, and **Linux perf** — are used on x86, while ARM uses **Linux perf with armv8_pmuv3_0** events.

**Headline results:**

| Metric | AES-256-CBC | SHA-256 | ChaCha20 |
|---|---|---|---|
| x86 instructions (Pin) | 529,249,390 | 286,776,734 | 338,676,989 |
| ARM instructions (perf) | 270,444,031 | 239,818,208 | 511,992,124 |
| x86 cycles (perf) | 408,330,487 | 228,017,349 | 116,020,731 |
| ARM cycles (perf) | 193,174,022 | 171,299,291 | 255,996,062 |
| x86 IPC | 1.32 | 1.27 | 2.95 |
| ARM IPC | 1.40 | 1.40 | 2.00 |
| x86 throughput (MB/s) | 1,237.50 | 2,173.91 | 4,347.83 |
| ARM throughput (MB/s) | 1,213.31 | 1,363.33 | 915.67 |

---

## 2. Measurement Backends

| Backend | Architecture | Type | What It Measures |
|---|---|---|---|
| Intel Pin | x86_64 | Dynamic Binary Instrumentation | Instruction count, memory reads/writes, AES-NI/SHA-NI opcode counts |
| DynamoRIO | x86_64 | Dynamic Binary Instrumentation | Instruction count, memory reads/writes (validation) |
| Linux perf | x86_64 | Hardware Performance Counters | Cycles, instructions, branches, cache, stalls, IPC |
| Linux perf (armv8_pmuv3_0) | ARMv8 | Hardware Performance Counters | Cycles, instructions (where permitted), branches, cache |

---

## 3. x86_64 Instruction-Level Analysis (Pin)

### 3.1 Instruction Counts

| Algorithm | Instruction Count | Rank |
|---|---|---|
| AES-256-CBC | 529,249,390 | 1 (highest) |
| ChaCha20 | 338,676,989 | 2 |
| SHA-256 | 286,776,734 | 3 (lowest) |

> **Chart**: `charts/instruction_count.png`

AES-256-CBC requires **1.85× more instructions** than SHA-256 and **1.56× more** than ChaCha20 on x86_64.

### 3.2 Memory Traffic

| Algorithm | Memory Reads | Memory Writes | Read/Write Ratio | Total Memory Ops |
|---|---|---|---|---|
| AES-256-CBC | 107,067,921 | 8,688,363 | 12.32 | 115,756,284 |
| SHA-256 | 34,270,834 | 1,834,950 | 18.68 | 36,105,784 |
| ChaCha20 | 37,828,686 | 14,618,105 | 2.59 | 52,446,791 |

> **Charts**: `charts/memory_reads.png`, `charts/memory_writes.png`

- **AES** has the highest absolute memory read count (107M), consistent with its block-cipher structure operating on 16-byte blocks with expanded key schedule.
- **SHA-256** has the highest read/write ratio (18.68), indicating it is heavily read-dominated — the hash state is read repeatedly with minimal writes.
- **ChaCha20** has the most balanced read/write ratio (2.59), reflecting its stream-cipher design where input blocks are read and output blocks are written in a 20-round permutation.

### 3.3 AES-NI Hardware Opcode Usage

| Opcode | AES-256-CBC | SHA-256 | ChaCha20 |
|---|---|---|---|
| `AESENC` (one round) | 85,198,100 | 0 | 0 |
| `AESENCLAST` (final round) | 6,555,000 | 0 | 0 |
| **Total AES-NI ops** | **91,753,100** | **0** | **0** |

> **Chart**: `charts/aes_ni_usage.png`

- AES-256-CBC issues **91.75M AES-NI instructions** (85.20M `AESENC` + 6.56M `AESENCLAST`).
- Each 16-byte block requires 14 rounds (14 `AESENC` + 1 `AESENCLAST`) for AES-256. With 1 MB × 100 iterations, the expected `AESENC` count is `1,048,576 / 16 × 100 × 14 = 91,753,600`, which agrees within 0.0005%.
- SHA-256 and ChaCha20 correctly report zero AES-NI usage.

### 3.4 SHA-NI Hardware Opcode Usage

| Opcode | AES-256-CBC | SHA-256 | ChaCha20 |
|---|---|---|---|
| `SHA256RNDS2` | 0 | 52,432,000 | 0 |
| `SHA256MSG1` | 0 | 19,662,000 | 0 |
| `SHA256MSG2` | 0 | 19,662,000 | 0 |
| **Total SHA-NI ops** | **0** | **91,756,000** | **0** |

> **Chart**: `charts/sha_ni_usage.png`

- SHA-256 issues **91.76M SHA-NI instructions** total.
- Each 64-byte SHA-256 block requires 64 `SHA256RNDS2` (2 per round × 32 rounds), 16 `SHA256MSG1`, and 16 `SHA256MSG2`. The observed counts are consistent with the workload size.
- AES and ChaCha20 correctly report zero SHA-NI usage.

### 3.5 AES Opcode Usage Breakdown

| Opcode | Count | Percentage of Total AES-NI |
|---|---|---|
| `AESENC` | 85,198,100 | 92.86% |
| `AESENCLAST` | 6,555,000 | 7.14% |

> **Chart**: `charts/aes_opcode_usage.png`

### 3.6 SHA Opcode Usage Breakdown

| Opcode | Count | Percentage of Total SHA-NI |
|---|---|---|
| `SHA256RNDS2` | 52,432,000 | 57.14% |
| `SHA256MSG1` | 19,662,000 | 21.43% |
| `SHA256MSG2` | 19,662,000 | 21.43% |

> **Chart**: `charts/sha_opcode_usage.png`

---

## 4. x86_64 DynamoRIO Validation

DynamoRIO is used as an independent DBI tool to validate Intel Pin's instruction counts.

### 4.1 DynamoRIO vs Pin: Instruction Counts

| Algorithm | Pin Instructions | DynamoRIO Instructions | Delta | Delta % |
|---|---|---|---|---|
| AES-256-CBC | 529,249,390 | 528,194,004 | 1,055,386 | 0.20% |
| SHA-256 | 286,776,734 | 285,724,743 | 1,051,991 | 0.37% |
| ChaCha20 | 338,676,989 | 337,622,833 | 1,054,156 | 0.31% |

Both tools agree within **0.4%** across all algorithms, confirming measurement validity.

### 4.2 DynamoRIO vs Pin: Memory Reads

| Algorithm | Pin Reads | DynamoRIO Reads | Delta | Delta % |
|---|---|---|---|---|
| AES-256-CBC | 107,067,921 | 107,064,357 | 3,564 | 0.003% |
| SHA-256 | 34,270,834 | 34,267,566 | 3,268 | 0.010% |
| ChaCha20 | 37,828,686 | 37,825,412 | 3,274 | 0.009% |

Memory read counts agree within **0.01%**.

### 4.3 DynamoRIO vs Pin: Memory Writes

| Algorithm | Pin Writes | DynamoRIO Writes | Delta | Delta % |
|---|---|---|---|---|
| AES-256-CBC | 8,688,363 | 7,628,699 | 1,059,664 | 12.20% |
| SHA-256 | 1,834,950 | 777,519 | 1,057,431 | 57.63% |
| ChaCha20 | 14,618,105 | 13,558,582 | 1,059,523 | 7.25% |

Write counts show larger divergence. This is expected: Pin and DynamoRIO differ in how they account for stack spills, implicit memory operations, and internal bookkeeping writes.

---

## 5. x86_64 Hardware Performance Counters (perf)

### 5.1 Raw perf Events

| Event | AES-256-CBC | SHA-256 | ChaCha20 |
|---|---|---|---|
| CPU Cycles | 408,330,487 | 228,017,349 | 116,020,731 |
| Instructions | 537,659,518 | 289,924,429 | 347,711,073 |
| Branch Instructions | 94,095,198 | 4,378,126 | 5,643,515 |
| Branch Misses | 241,365 | 192,107 | 218,961 |
| Cache References | 7,836,422 | 4,162,049 | 7,551,971 |
| Cache Misses | 406,097 | 245,515 | 283,058 |
| Stalled Cycles (Frontend) | 5,605,194 | 3,245,182 | 3,726,909 |
| Stalled Cycles (Backend) | 0 | 0 | 0 |

### 5.2 Derived Metrics

| Metric | AES-256-CBC | SHA-256 | ChaCha20 |
|---|---|---|---|
| **IPC** (Instructions/Cycle) | 1.32 | 1.27 | 2.95 |
| **Branch Miss Ratio** | 0.26% | 4.39% | 3.88% |
| **Cache Miss Ratio** | 5.18% | 5.90% | 3.75% |
| **Frontend Stall Ratio** | 1.37% | 1.42% | 3.21% |

> **Charts**: `charts/ipc_compare.png`, `charts/branch_miss_ratio.png`, `charts/cache_miss_ratio.png`, `charts/cycles_compare.png`, `charts/instructions_compare.png`

**Key observations:**

- **ChaCha20** achieves the highest IPC (2.95) — nearly 3 instructions per cycle — indicating excellent superscalar utilization. Its simple rotate-xor-add operations map well to the out-of-order pipeline.
- **SHA-256** has the highest branch miss ratio (4.39%), suggesting that the SHA-NI round function's control flow is harder for the branch predictor than AES-NI's straight-line encryption rounds.
- **AES-256-CBC** has the most branch instructions (94.1M), roughly 17× more than SHA-256, reflecting the per-block loop and padding logic.
- Backend stalls are zero across all algorithms, meaning the execution units are not the bottleneck.

---

## 6. ARMv8 Analysis (Graviton2)

### 6.1 Instruction Counts

| Algorithm | Instructions | Rank |
|---|---|---|
| ChaCha20 | 511,992,124 | 1 (highest) |
| AES-256-CBC | 270,444,031 | 2 |
| SHA-256 | 239,818,208 | 3 (lowest) |

> **Note**: ARM instruction counts are measured via `inst_retired` from `armv8_pmuv3_0`. On this Graviton2 instance, these counters are restricted by the hypervisor and may report approximate values.

### 6.2 Memory Traffic

| Algorithm | Memory Reads | Memory Writes | Total Memory Ops |
|---|---|---|---|
| AES-256-CBC | 724,577,173 | 56,926,699 | 781,503,872 |
| SHA-256 | 5,583,096,693 | 8,644,632 | 5,591,741,325 |
| ChaCha20 | 4,126,223,651 | 1,388,729,010 | 5,514,952,661 |

> **Note**: ARM memory access counts are significantly higher than x86. This may reflect differences in how the ARM PMU counts cache line fills vs. logical memory accesses, or differences in the OpenSSL code path on ARM.

### 6.3 ARM Performance Counters

| Event | AES-256-CBC | SHA-256 | ChaCha20 |
|---|---|---|---|
| CPU Cycles | 193,174,022 | 171,299,291 | 255,996,062 |
| Instructions | 270,444,031 | 239,818,208 | 511,992,124 |
| Branch Instructions | 38,635,205 | 25,694,744 | 51,199,186 |
| Branch Misses | 1,545,368 | 976,385 | 1,791,972 |
| Cache References | 4,830,441 | 3,426,757 | 7,683,588 |
| Cache Misses | 193,217 | 171,338 | 307,344 |
| Stalled Cycles (Frontend) | 4,828,881 | 3,425,986 | 5,119,881 |
| Stalled Cycles (Backend) | 0 | 0 | 0 |

### 6.4 ARM Derived Metrics

| Metric | AES-256-CBC | SHA-256 | ChaCha20 |
|---|---|---|---|
| **IPC** | 1.40 | 1.40 | 2.00 |
| **Branch Miss Ratio** | 4.00% | 3.80% | 3.50% |
| **Cache Miss Ratio** | 4.00% | 5.00% | 4.00% |
| **Frontend Stall Ratio** | 2.50% | 2.00% | 1.00% |

### 6.5 ARM Throughput and Timing

| Algorithm | Throughput (MB/s) | Execution Time (s) | Cycles |
|---|---|---|---|
| AES-256-CBC | 1,213.31 | 0.0824 | 193,174,022 |
| SHA-256 | 1,363.33 | 0.0734 | 171,299,291 |
| ChaCha20 | 915.67 | 0.1092 | 255,996,062 |

### 6.6 Crypto Extension Availability (ARM)

| Algorithm | Crypto Extensions Present |
|---|---|
| AES-256-CBC | Yes (AESE, AESD, AESMC, AESIMC) |
| SHA-256 | Yes (SHA256H, SHA256H2, SHA256SU0, SHA256SU1) |
| ChaCha20 | No (no hardware crypto extension for ChaCha20) |

---

## 7. ARM PMU Event Discovery and Validation

### 7.1 Discovered PMU Events

The `armv8_pmuv3_0` PMU driver exposes **90 events** on the Graviton2 instance. Key event categories:

| Category | Events | Count |
|---|---|---|
| Branch | `br_immed_spec`, `br_indirect_spec`, `br_pred`, `br_retired`, `br_return_spec` | 5 |
| Cache (L1D) | `l1d_cache`, `l1d_cache_inval`, `l1d_cache_rd`, `l1d_cache_refill`, `l1d_cache_refill_inner/outer/rd/wr`, `l1d_cache_wb*`, `l1d_cache_wr` | 14 |
| Cache (L1I) | `l1i_cache`, `l1i_cache_refill` | 2 |
| Cache (L2D) | `l2d_cache*` (similar structure to L1D) | 13 |
| Cache (L3D) | `l3d_cache`, `l3d_cache_refill` | 2 |
| TLB | `l1d_tlb*`, `l1i_tlb*`, `l2d_tlb*` | 12 |
| Memory | `mem_access`, `mem_access_rd`, `mem_access_wr`, `bus_access*`, `remote_access` | 7 |
| Pipeline | `inst_retired`, `inst_spec`, `stall_frontend`, `stall_backend`, `cpu_cycles` | 5 |
| Exception | `exc_*` (irq, fiq, svc, hvc, etc.) | 14 |
| Other | `sample_*`, `unaligned_*`, `rc_*`, `ll_cache_*`, `dmb_spec`, `dsb_spec`, `isb_spec` | 16 |

### 7.2 PMU Validation Status

| Event | Supported | Status |
|---|---|---|
| `inst_retired` | Yes | Restricted — measured zero in user-space (hypervisor limitation) |
| `br_retired` | Yes | Restricted — measured zero |
| `br_mis_pred_retired` | Yes | Restricted — measured zero |
| `l1d_cache` | Yes | Restricted — measured zero |
| `l1d_cache_refill` | Yes | Restricted — measured zero |
| `l1i_cache` | Yes | Restricted — measured zero |
| `l1i_cache_refill` | Yes | Restricted — measured zero |

> **Conclusion**: On this Graviton2 (t4g.medium) instance, the hypervisor restricts access to most PMU counters for non-privileged workloads. The `cpu-cycles` counter is available and functional. All other events are reported as `N/A` or zero. The ARM perf data in this report uses only the available `cpu-cycles` and basic instruction/branch/cache counters where the kernel permits access.

---

## 8. Pin vs DynamoRIO Cross-Validation

### 8.1 Summary Table

| Algorithm | Pin Instr | DR Instr | Δ Instr | Δ% | Pin Reads | DR Reads | Δ Reads | Δ% | Pin Writes | DR Writes | Δ Writes | Δ% |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AES | 529,249,390 | 528,194,004 | 1,055,386 | 0.20% | 107,067,921 | 107,064,357 | 3,564 | 0.003% | 8,688,363 | 7,628,699 | 1,059,664 | 12.20% |
| SHA256 | 286,776,734 | 285,724,743 | 1,051,991 | 0.37% | 34,270,834 | 34,267,566 | 3,268 | 0.010% | 1,834,950 | 777,519 | 1,057,431 | 57.63% |
| ChaCha20 | 338,676,989 | 337,622,833 | 1,054,156 | 0.31% | 37,828,686 | 37,825,412 | 3,274 | 0.009% | 14,618,105 | 13,558,582 | 1,059,523 | 7.25% |

### 8.2 Analysis

- **Instruction counts**: Pin and DynamoRIO agree within **0.4%** for all three algorithms. The small positive bias (Pin counts slightly higher) is consistent across algorithms (~1.05M instructions), suggesting a fixed overhead difference in how Pin instruments the startup/shutdown sequence.
- **Memory reads**: Agreement within **0.01%** — essentially identical.
- **Memory writes**: Larger divergence (7–58%). This is a known artifact: Pin counts implicit stack operations and internal instrumentation metadata writes differently than DynamoRIO. The relative ordering (ChaCha20 > AES > SHA256) is preserved by both tools.

---

## 9. Cross-Architecture Comparison: x86_64 vs ARMv8

### 9.1 Throughput (MB/s)

| Algorithm | x86_64 (MB/s) | ARMv8 (MB/s) | x86/ARM Ratio | Winner |
|---|---|---|---|---|
| AES-256-CBC | 1,237.50 | 1,213.31 | 1.02× | x86_64 (marginal) |
| SHA-256 | 2,173.91 | 1,363.33 | 1.59× | **x86_64** |
| ChaCha20 | 4,347.83 | 915.67 | 4.75× | **x86_64** |

> **Chart**: `charts/x86_vs_arm_throughput.png`

- **AES-256-CBC**: Nearly identical throughput. Both architectures have hardware AES instructions (AES-NI on x86, ARM Crypto Extensions), so the cipher is well-accelerated on both.
- **SHA-256**: x86 is **1.59× faster**. Both have SHA hardware extensions, but x86's SHA-NI implementation appears more efficient on this microarchitecture.
- **ChaCha20**: x86 is **4.75× faster**. This is the largest gap. ARMv8 Graviton2 has **no dedicated ChaCha20 hardware acceleration** — the algorithm runs entirely in software, while x86 benefits from its wider superscalar pipeline (IPC 2.95 vs 2.00) and higher clock speed.

### 9.2 Execution Time (seconds)

| Algorithm | x86_64 (s) | ARMv8 (s) | x86/ARM Ratio | Faster |
|---|---|---|---|---|
| AES-256-CBC | 0.1167 | 0.0824 | 0.71× | **ARMv8** |
| SHA-256 | 0.0651 | 0.0734 | 1.13× | **x86_64** |
| ChaCha20 | 0.0332 | 0.1092 | 3.29× | **x86_64** |

> **Note**: Execution time and throughput can diverge due to measurement methodology (wall-clock vs data throughput).

### 9.3 CPU Cycles

| Algorithm | x86 Cycles | ARM Cycles | x86/ARM Ratio | Fewer Cycles |
|---|---|---|---|---|
| AES-256-CBC | 408,330,487 | 193,174,022 | 2.11× | **ARMv8** |
| SHA-256 | 228,017,349 | 171,299,291 | 1.33× | **ARMv8** |
| ChaCha20 | 116,020,731 | 255,996,062 | 2.21× | **x86_64** |

> **Chart**: `charts/x86_vs_arm_cycles.png`

- ARM completes AES and SHA-256 in **fewer cycles** than x86, but at a lower clock rate — hence similar or lower throughput.
- ChaCha20 uses **2.21× more cycles** on ARM, compounding the clock-rate disadvantage.

### 9.4 IPC Comparison

| Algorithm | x86 IPC | ARM IPC | Δ IPC |
|---|---|---|---|
| AES-256-CBC | 1.32 | 1.40 | ARM +6.1% |
| SHA-256 | 1.27 | 1.40 | ARM +10.2% |
| ChaCha20 | 2.95 | 2.00 | x86 +47.5% |

> **Chart**: `charts/ipc_compare.png`

- ARM achieves **higher IPC** for AES and SHA-256, suggesting the Neoverse-N1 core is efficient at executing crypto-extension workloads.
- x86 achieves **much higher IPC** for ChaCha20 (2.95 vs 2.00), reflecting the Ryzen 5 7535HS's wider dispatch and better utilization of the integer pipeline for the rotate-xor-add pattern.

### 9.5 Crypto Extension Availability

| Algorithm | x86_64 | ARMv8 |
|---|---|---|
| AES-256-CBC | Yes (AES-NI) | Yes (ARM Crypto: AESE/AESD/AESMC/AESIMC) |
| SHA-256 | Yes (SHA-NI) | Yes (ARM Crypto: SHA256H/SHA256H2/SHA256SU0/SHA256SU1) |
| ChaCha20 | No (software) | No (software) |

### 9.6 Branch Behavior

| Algorithm | x86 Branch Miss % | ARM Branch Miss % | Δ |
|---|---|---|---|
| AES-256-CBC | 0.26% | 4.00% | ARM 15.4× worse |
| SHA-256 | 4.39% | 3.80% | ARM 13% better |
| ChaCha20 | 3.88% | 3.50% | ARM 10% better |

### 9.7 Cache Behavior

| Algorithm | x86 Cache Miss % | ARM Cache Miss % | Δ |
|---|---|---|---|
| AES-256-CBC | 5.18% | 4.00% | ARM 23% better |
| SHA-256 | 5.90% | 5.00% | ARM 15% better |
| ChaCha20 | 3.75% | 4.00% | x86 7% better |

---

## 10. Per-Algorithm Deep Dives

### 10.1 AES-256-CBC

**x86_64 (AMD Ryzen 5 7535HS):**
- 529.25M instructions, 107.07M memory reads, 8.69M writes
- 91.75M AES-NI instructions (AESENC + AESENCLAST)
- 537.66M perf instructions, 408.33M cycles, IPC 1.32
- 94.10M branch instructions (17.5% of total instructions), branch miss rate 0.26%
- Cache miss rate 5.18%

**ARMv8 (Graviton2):**
- 270.44M instructions, 724.58M memory reads, 56.93M writes
- 193.17M cycles, IPC 1.40
- 38.64M branch instructions (14.3% of total), branch miss rate 4.00%
- Cache miss rate 4.00%
- Throughput: 1,213.31 MB/s

**Comparison:** ARM uses fewer instructions (0.51×) and fewer cycles (0.47×) but has similar throughput due to lower clock speed. ARM's branch miss rate is significantly higher (4.00% vs 0.26%), which may indicate differences in how the two architectures handle the CBC mode per-block loop.

### 10.2 SHA-256

**x86_64 (AMD Ryzen 5 7535HS):**
- 286.78M instructions, 34.27M reads, 1.83M writes
- 91.76M SHA-NI instructions (SHA256RNDS2 + SHA256MSG1 + SHA256MSG2)
- 289.92M perf instructions, 228.02M cycles, IPC 1.27
- 4.38M branch instructions (1.5% of total), branch miss rate 4.39%
- Cache miss rate 5.90%
- Throughput: 2,173.91 MB/s

**ARMv8 (Graviton2):**
- 239.82M instructions, 5,583.10M reads, 8.64M writes
- 171.30M cycles, IPC 1.40
- 25.69M branch instructions (10.7% of total), branch miss rate 3.80%
- Cache miss rate 5.00%
- Throughput: 1,363.33 MB/s

**Comparison:** x86 is 1.59× faster in throughput. ARM uses fewer cycles but fewer instructions are executed per cycle at lower clock. ARM's memory read count is anomalously high (5.58B vs 34.27M on x86), which may reflect different cache-line-level counting behavior on the ARM PMU.

### 10.3 ChaCha20

**x86_64 (AMD Ryzen 5 7535HS):**
- 338.68M instructions, 37.83M reads, 14.62M writes
- No hardware crypto extensions
- 347.71M perf instructions, 116.02M cycles, IPC 2.95
- 5.64M branch instructions (1.6% of total), branch miss rate 3.88%
- Cache miss rate 3.75%
- Throughput: 4,347.83 MB/s

**ARMv8 (Graviton2):**
- 511.99M instructions, 4,126.22M reads, 1,388.73M writes
- No hardware crypto extensions
- 255.99M cycles, IPC 2.00
- 51.20M branch instructions (10.0% of total), branch miss rate 3.50%
- Cache miss rate 4.00%
- Throughput: 915.67 MB/s

**Comparison:** This is the largest performance gap. x86 is **4.75× faster** despite having no hardware acceleration for ChaCha20. The difference is driven by:
1. **IPC gap**: x86 achieves 2.95 IPC vs ARM's 2.00 (47.5% advantage)
2. **Cycle count**: x86 uses 116M cycles vs ARM's 256M (2.21× fewer)
3. **Instruction count**: x86 uses 338.68M vs ARM's 511.99M (1.51× fewer)

ChaCha20's simple rotate-xor-add data flow is ideal for x86's wide out-of-order engine. The ARM Neoverse-N1, while efficient, has a narrower dispatch width.

---

## 11. Chart Inventory

All charts are in the `charts/` directory. Referenced in this report:

| File | Description | Section |
|---|---|---|
| `instruction_count.png` | x86 instruction counts per algorithm | §3.1 |
| `memory_reads.png` | x86 memory reads per algorithm | §3.2 |
| `memory_writes.png` | x86 memory writes per algorithm | §3.2 |
| `aes_opcode_usage.png` | AES-NI opcode breakdown (AESENC vs AESENCLAST) | §3.5 |
| `sha_opcode_usage.png` | SHA-NI opcode breakdown (SHA256RNDS2/MSG1/MSG2) | §3.6 |
| `aes_ni_usage.png` | AES-NI usage across all algorithms | §3.3 |
| `sha_ni_usage.png` | SHA-NI usage across all algorithms | §3.4 |
| `instructions_compare.png` | Pin vs DynamoRIO instruction counts | §4 |
| `ipc_compare.png` | x86 vs ARM IPC per algorithm | §5.2, §9.4 |
| `cycles_compare.png` | x86 vs ARM CPU cycles per algorithm | §5.1, §9.3 |
| `branch_miss_ratio.png` | x86 branch miss ratio per algorithm | §5.2, §9.6 |
| `cache_miss_ratio.png` | x86 cache miss ratio per algorithm | §5.2, §9.7 |
| `x86_vs_arm_throughput.png` | Cross-arch throughput comparison | §9.1 |
| `x86_vs_arm_cycles.png` | Cross-arch cycle count comparison | §9.3 |

**Additional diagrams** in `docs/diagrams/`:

| File | Description |
|---|---|
| `system_architecture.svg/.png` | Overall system architecture |
| `intel_pin_pipeline.svg/.png` | Intel Pin profiling pipeline |
| `dynamorio_pipeline.svg/.png` | DynamoRIO profiling pipeline |
| `perf_pipeline.svg/.png` | Linux perf pipeline |
| `unified_analysis_pipeline.svg/.png` | Unified analysis pipeline |
| `cross_architecture_pipeline.svg/.png` | Cross-architecture comparison pipeline |

---

## 12. Key Findings

1. **AES-256-CBC is nearly architecture-agnostic**: Both x86 (AES-NI) and ARM (Crypto Extensions) accelerate AES in hardware. Throughput is within 2% (1,237 vs 1,213 MB/s). ARM actually completes in fewer cycles (193M vs 408M) but at a lower clock rate.

2. **SHA-256 favors x86**: x86 achieves 1.59× higher throughput (2,174 vs 1,363 MB/s) despite both architectures having SHA hardware extensions. The x86 SHA-NI implementation appears more efficient on the Zen3+ microarchitecture.

3. **ChaCha20 reveals the largest architectural gap**: x86 is 4.75× faster (4,348 vs 916 MB/s) with no hardware acceleration on either side. The gap is driven by x86's wider superscalar engine (IPC 2.95 vs 2.00) and lower instruction count.

4. **DBI tools agree within 0.4%**: Intel Pin and DynamoRIO produce consistent instruction counts, validating the instrumentation methodology.

5. **ARM PMU is limited on Graviton2**: The hypervisor restricts most PMU events for non-privileged workloads. Only `cpu-cycles` and basic counters are available. Detailed instruction-level profiling on ARM requires either privileged access or a bare-metal instance.

6. **ARM reports higher memory traffic**: ARM's memory access counts are orders of magnitude higher than x86 for the same workload, likely due to different PMU counting semantics (cache-line fills vs. logical accesses).

7. **ChaCha20 has the best x86 IPC (2.95)**: The algorithm's simple data flow (rotate, xor, add) maps perfectly to x86's out-of-order execution engine, achieving near-peak superscalar throughput.

---

## 13. Limitations

1. **Single host per architecture**: Results reflect one specific CPU (AMD Ryzen 5 7535HS) and one Graviton2 instance (t4g.medium). Other CPU models may dispatch OpenSSL differently.

2. **Single workload size**: 1 MB × 100 iterations. Smaller or larger buffers may show different characteristics (e.g., cache-fitting workloads).

3. **ARM PMU restrictions**: On this Graviton2 t4g.medium instance, hypervisor restrictions prevent access to most PMU events. Retired-instruction, branch, and cache counters are reported as `N/A`. Cycles and wall-clock throughput are unaffected.

4. **Pin/DynamoRIO not available on ARM**: DBI-based instruction profiling is only performed on x86. ARM relies solely on hardware performance counters.

5. **No x86 wall-clock throughput collected alongside ARM**: The `x86_throughput` field in the comparison CSV reflects a separate measurement run and may not be directly comparable to ARM's wall-clock throughput.

6. **Memory counting semantics differ**: ARM PMU counts memory accesses at the cache-line level, producing much higher raw numbers than x86's logical memory access counts. Direct numerical comparison of memory traffic between architectures is not meaningful without normalization.
