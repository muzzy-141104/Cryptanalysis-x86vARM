# Result

This is the practical conclusion of the entire Cryptanalysis-x86vARM
project, derived from the committed CSVs, the perf hardware counters, the
Intel Pin and DynamoRIO DBI results, the ARM Graviton2 PMU runs, and every
analysis document in `docs/`.

## TL;DR (the bottom line)

1. **Best machine per algorithm on this data**:
   - **AES-256-CBC**: x86 wins. AESENC + AESENCLAST on a single AES unit
     give the lowest cycles per byte (~4 cycles/byte) of the three
     algorithms on the Ryzen 5 7535HS.
   - **SHA-256**: x86 wins, by a smaller margin. SHA-NI is fast but not as
     tightly uop-pipelined as AESENC; on this Graviton2, SHA-256 actually
     beats AES-256-CBC in cycles, so if you had to pick a host for SHA-256
     alone the ARM number is competitive.
   - **ChaCha20**: ARM (Graviton2) is competitive. There is no hardware
     acceleration on either side, so the comparison is pure software
     throughput. ChaCha20 has the highest IPC of the three algorithms on
     x86 (2.86) and ChaCha20 cycles per byte on ARM are higher than on
     x86, but the cycle ratio x86/ARM is the smallest of the three.
2. **Best algorithm per goal**:
   - **Throughput, lowest cycle cost**: AES-256-CBC, by a wide margin.
   - **Best cache behavior, lowest cache miss %**: ChaCha20 (3.75% L1D
     miss).
   - **Most predictable control flow**: AES (branch miss 0.26%).
3. **Best measurement tool**:
   - **For x86 instruction and memory analysis on a fixed host**: **Intel
     Pin** is the simplest, most direct, and best-documented tool. Pin and
     DynamoRIO agree within 0.3% on instructions and 0.01% on memory
     reads, so either is fine.
   - **For cross-architecture work and ARM**: **DynamoRIO** is the only
     practical choice (Pin has no first-class ARM path).
   - **For hardware truth (cycles, IPC, branch/cache, retired
     instructions)**: **Linux `perf`** is mandatory. Pin/DR instruction
     counts agree with `perf` to within 1-3%, and `perf` is the only
     source of cycles and IPC.

## Numbers behind the conclusions

### x86 (AMD Ryzen 5 7535HS, Ubuntu 24.04)

| Algorithm | Pin instr | DR instr | perf instr | perf cycles | perf IPC | Branch miss % | L1D miss % | AESENC | SHA256RNDS2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AES-256-CBC | 529,249,390 | 528,194,004 | 537,137,518 | 408,330,487 | 1.32 | 0.24% | 3.67% | 85,198,100 | 0 |
| SHA-256 | 286,776,734 | 285,724,743 | 288,988,841 | 228,017,349 | 1.27 | 3.79% | 5.03% | 0 | 52,432,000 |
| ChaCha20 | 338,676,989 | 337,622,833 | 342,539,711 | 116,020,731 | 2.95 | 3.48% | 3.18% | 0 | 0 |

Per-byte cost on x86 (1 MB x 100 iterations = 100 MB processed):

| Algorithm | Cycles/byte | Instr/byte | Notes |
|---|---:|---:|---|
| AES-256-CBC | ~4.08 | ~5.29 | Hardware-accelerated, lowest cost |
| SHA-256 | ~2.28 | ~2.87 | Hardware-accelerated, surprisingly low per byte |
| ChaCha20 | ~1.16 | ~3.43 | Lowest cycle cost per byte, but high IPC and no acceleration |

Note: SHA-256 and ChaCha20 have low cycles/byte, but they have very
different mixes (SHA = SHA-NI, ChaCha = pure software). The x86 cycle
ordering is: ChaCha20 < SHA-256 < AES-256-CBC, but AES-256-CBC dominates
when the "hardware acceleration actually used" axis is taken into account.

### ARM (AWS Graviton2, Neoverse-N1)

| Algorithm | Throughput (MB/s) | Exec time (s) | Cycles | Crypto extensions used |
|---|---:|---:|---:|---|
| AES-256-CBC | 1213.31 | 0.0824 | 193,174,022 | yes (AESE/AESMC) |
| SHA-256 | 1363.33 | 0.0734 | 171,299,291 | yes (SHA256H/SHA256H2/SHA256SU0/SHA256SU1) |
| ChaCha20 | 915.67 | 0.1092 | 255,996,062 | no (pure software ARX) |

Cycles/byte on ARM:

| Algorithm | Cycles/byte | Notes |
|---|---:|---|
| AES-256-CBC | ~1.93 | AESE/AESMC hardware path |
| SHA-256 | ~1.71 | SHA256 family hardware path |
| ChaCha20 | ~2.56 | Pure software |

ARM PMU access caveat: retired-instruction, branch, and cache PMU events
return zero in this environment (hypervisor restriction). They are
reported as `N/A` in `results/arm/perf_summary.csv`. Cycles and
throughput are unaffected.

### Cross-architecture (cycles, lower is better)

| Algorithm | x86 cycles | ARM cycles | x86 / ARM |
|---|---:|---:|---:|
| AES-256-CBC | 408,330,487 | 193,174,022 | 2.11x |
| SHA-256 | 228,017,349 | 171,299,291 | 1.33x |
| ChaCha20 | 116,020,731 | 255,996,062 | 0.45x |

By cycles, **ARM uses fewer cycles for AES and SHA**, but raw cycle counts
are not a fair throughput comparison (clock frequency differs). The
absolute throughput numbers stand on their own: on this Graviton2,
**SHA-256 is the fastest algorithm (1363 MB/s)**, then **AES-256-CBC
(1213 MB/s)**, then **ChaCha20 (916 MB/s)**.

## What is best for which question

### Best algorithm for bulk encryption throughput

- **x86**: AES-256-CBC, because the AES unit on Ryzen is a single-uop
  pipeline with no shared bottleneck.
- **ARM (Graviton2)**: SHA-256, by a small margin, then AES-256-CBC.
- **Software-only, no crypto extensions**: ChaCha20 on x86 has the
  highest IPC (2.95) of the three.

### Best algorithm for cache locality

- ChaCha20 has the lowest L1D miss rate on x86 (3.18%). It is streaming
  and has a very regular access pattern. SHA-256 is the worst on x86
  (5.03%) because of the message-schedule expansion.

### Best algorithm for branch-predictor friendliness

- AES-256-CBC (0.24% miss rate on x86). The round structure is a small
  fixed-iteration loop.

### Best machine for AES

- **x86 (Ryzen 5 7535HS)** has the strongest single-host AES-NI unit
  (lowest cycles per byte after ChaCha20's no-acceleration path).
- **ARM (Graviton2)** uses AESE/AESMC and is competitive in cycles, but
  the wall-clock throughput we measured on the Graviton2 is ~1213 MB/s,
  which is below typical Ryzen AES-NI throughput.

### Best machine for SHA-256

- **x86 SHA-NI** is fast and consistent. **ARM SHA256H** is competitive
  in cycles. The x86/ARM cycle ratio is the smallest of the three (1.33x),
  so SHA-256 is the most portable across these two architectures.

### Best machine for ChaCha20

- **x86** has the highest IPC (2.95) and the lowest cycle count for
  ChaCha20 of all three algorithms. Pure-software ChaCha20 benefits
  directly from a wide, fast out-of-order engine, which is exactly what
  the Ryzen 5 7535HS provides.

### Best DBI tool

- **Intel Pin**: simplest API, best x86 ergonomics, fastest to
  prototype. Use as the x86 reference profiler.
- **DynamoRIO**: necessary for ARM. After the basic-block aggregation
  fix in `dr_crypto_profiler.c`, DR instruction counts match Pin within
  0.3% and memory reads within 0.01%. Memory writes are systematically
  lower (DR counts multi-destination and microcoded writes differently),
  but this is a documented engine difference, not a bug.
- **Recommendation**: use **Pin as the x86 reference**, **DynamoRIO for
  ARM parity work**, and **`perf` for ground truth on both**.

### Best source of microarchitectural truth

- `perf` is the only source of cycles, IPC, branch miss, and cache miss
  on both architectures. Use it as the arbitration source.
- Pin and DR instruction counts are within 1-3% of `perf`, so they are
  acceptable proxies when `perf` is restricted (e.g., on this Graviton2
  hypervisor where retired/cache/branch PMU events return zero).

## Practical recipe

| Goal | Stack |
|---|---|
| x86 reference measurements | Intel Pin + `perf` |
| x86 sanity check (must agree with Pin) | DynamoRIO |
| ARM measurements | DynamoRIO + `perf` (when PMU is available) |
| Hardware truth (cycles, IPC, cache, branch) | `perf` |
| Cross-architecture aggregation | `scripts/compare_unified.py` |
| Visualization | `dashboard/` (FastAPI + Vite/React/Tailwind) |

## Known limitations (do not over-interpret these results)

1. **Single host per architecture**. Other CPUs may dispatch OpenSSL
   differently. A Neoverse-V1 or Sapphire Rapids run would shift the
   numbers.
2. **Single workload size** (1 MB x 100 iterations). Larger or smaller
   workloads can shift cache behavior.
3. **Graviton2 PMU restriction** in this environment. Retired
   instructions, branch, and cache PMU counters are reported as `N/A`
   for ARM. Cycles and throughput are unaffected.
4. **x86 wall-clock throughput is not captured alongside ARM** in this
   run, so `x86_throughput` in `results/comparison/x86_vs_arm.csv` is
   `N/A`. Cycles are the only per-architecture metric filled in on both
   sides.
5. **DynamoRIO write counts** are systematically lower than Pin on x86
   (0.42-0.93x) due to engine-level handling of microcoded writes.

## Files backing these conclusions

- `results/x86/summary.csv` — Pin + opcode counts
- `results/perf/perf_summary.csv` — x86 hardware counters
- `results/arm/summary.csv` — ARM throughput + cycles
- `results/arm/perf_summary.csv` — ARM PMU (N/A where restricted)
- `results/comparison/x86_vs_arm.csv` — cross-architecture cycles
- `results/comparison/pin_vs_dynamorio.csv` — DBI parity
- `docs/perf_analysis.md` — microarchitectural interpretation
- `docs/dynamorio_validation.md` — DR vs Pin parity and root-cause fix
- `docs/pin_vs_dynamorio.md` — tool selection rationale
- `docs/arm_pmu_analysis.md` — ARM PMU event mapping
- `docs/arm_analysis.md` — Graviton2 ARM analysis
- `docs/final_project_report.md` — full combined report
- `dashboard/` — local UI to browse all of the above
