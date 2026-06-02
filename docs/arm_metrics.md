# ARM Metrics Definition

This document defines the metrics that will be collected on the ARM target. The goal is to keep the metric schema identical to x86 wherever possible, so that the unified comparison (`results/comparison/unified_comparison.csv`) is meaningful.

## 1. Common metrics (same on x86 and ARM)

| Metric | Source | Description |
|---|---|---|
| instruction_count | DynamoRIO | App instruction count |
| memory_reads | DynamoRIO | `instr_reads_memory()` hits |
| memory_writes | DynamoRIO | `instr_writes_memory()` hits |
| cpu-cycles | perf | CPU cycles (event `cpu-cycles` on ARM: `cpu_cycles` PMU event) |
| instructions | perf | Hardware `instructions` event |
| branch-instructions | perf | `br_inst_retired` (ARM) |
| branch-misses | perf | `br_mis_pred` (ARM) |
| cache-references | perf | `L1D_CACHE_REFILL` (ARM) or `L1D_CACHE` (architectural) |
| cache-misses | perf | `L1D_CACHE_REFILL` (ARM) |
| ipc | derived | `instructions / cycles` |
| branch_miss_ratio | derived | `branch-misses / branch-instructions` |
| cache_miss_ratio | derived | `cache-misses / cache-references` |

ARM `perf` event names use underscores (e.g. `cpu_cycles`, `br_mis_pred`) on most platforms; some kernels expose them with hyphens too. The parser maps both forms.

## 2. ARM AES extension metrics

ARMv8 AES extension opcodes (AArch64):

| Opcode | Mnemonic | Description |
|---|---|---|
| AESE | AESE Qd, Qn | AES single round encryption |
| AESD | AESD Qd, Qn | AES single round decryption |
| AESMC | AESMC Qd, Qn | AES mix columns |
| AESIMC | AESIMC Qd, Qn | AES inverse mix columns |

OpenSSL dispatches to the ARMv8 AES extension when the host advertises it (`/proc/cpuinfo` shows `aes`).

## 3. ARM SHA extension metrics

ARMv8 SHA-256 extension opcodes (AArch64):

| Opcode | Mnemonic | Description |
|---|---|---|
| SHA256H | SHA256H Qd, Qn, Qm | SHA-256 hash update, part 1 |
| SHA256H2 | SHA256H2 Qd, Qn, Qm | SHA-256 hash update, part 2 |
| SHA256SU0 | SHA256SU0 Qd, Qn | SHA-256 schedule update 0 |
| SHA256SU1 | SHA256SU1 Qd, Qn, Qm | SHA-256 schedule update 1 |

## 4. DynamoRIO client extension

The DynamoRIO client (`dynamorio_client/dr_crypto_profiler.c`) will be extended to recognize the ARMv8 opcodes using `instr_get_opcode()` and the DR IR `OP_*` definitions. Output rows to add to the per-algorithm CSV:

```
aese_count
aesd_count
aesmc_count
aesimc_count
sha256h_count
sha256h2_count
sha256su0_count
sha256su1_count
```

## 5. IPC comparison methodology

- Run identical drivers and workload on x86 and ARM.
- Capture `perf` events.
- Compute IPC for each algorithm.
- Compare:
  - x86 IPC vs ARM IPC
  - x86 instructions-per-byte vs ARM instructions-per-byte
  - x86 cycles-per-byte vs ARM cycles-per-byte

## 6. x86 vs ARM comparison methodology

For each algorithm (AES, SHA256, ChaCha20):

1. Same input size and iteration count.
2. Same OpenSSL version (compile on each host from the same upstream tag, or use distro packages with the same minor version).
3. Run three times on each host; report median values.
4. Capture both DynamoRIO and perf numbers.
5. Compute per-architecture throughput (MB/s) and cycles per byte.
6. Compute crypto-opcode counts: AESENC+AESENCLAST vs AESE+AESMC.

## 7. Output schemas

- `results/arm/aes_profile.csv` (DynamoRIO)
- `results/arm/sha256_profile.csv`
- `results/arm/chacha20_profile.csv`
- `results/arm/{aes,sha256,chacha20}_perf.csv`
- `results/arm/perf_summary.csv`
- `results/arm/summary.csv` (aggregated, same shape as `results/x86/summary.csv`)

All files are produced by the same Python scripts used on x86, with paths swapped.

## 8. Validation invariants

- AES: `aese_count > 0` on ARM (when running on Graviton/Ampere with aes flag)
- SHA256: `sha256h_count > 0` on ARM
- ChaCha20: no crypto-extension counts on either x86 or ARM
- Pin/DynamoRIO instruction counts agree to within 1% on ARM (the goal; subject to ARM-specific DBI behavior)
