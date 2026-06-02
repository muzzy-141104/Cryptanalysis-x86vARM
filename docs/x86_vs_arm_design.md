# x86 vs ARM Comparison Design (Future Phase)

This document is a design template for the cross-architecture comparison that will be produced in Phase 9 once ARM profiling data is available. The tables below specify the exact shape of the final comparison. Numeric values will be filled in after ARM profiling runs.

## 1. Throughput (MB/s)

| Algorithm | x86 MB/s | ARM MB/s | Ratio (x86 / ARM) |
|---|---:|---:|---:|
| AES-256-CBC | TBD | TBD | TBD |
| SHA256 | TBD | TBD | TBD |
| ChaCha20 | TBD | TBD | TBD |

Notes:
- Workload: 1 MB x 100 iterations on each host.
- Drivers identical source; compiled with `-O2` on each host.
- `ratio > 1` means x86 is faster.

## 2. Instruction count (DynamoRIO)

| Algorithm | x86 instr | ARM instr | Ratio (x86 / ARM) |
|---|---:|---:|---:|
| AES-256-CBC | TBD | TBD | TBD |
| SHA256 | TBD | TBD | TBD |
| ChaCha20 | TBD | TBD | TBD |

## 3. IPC (perf)

| Algorithm | x86 IPC | ARM IPC | Ratio (x86 / ARM) |
|---|---:|---:|---:|
| AES-256-CBC | TBD | TBD | TBD |
| SHA256 | TBD | TBD | TBD |
| ChaCha20 | TBD | TBD | TBD |

## 4. Cache miss ratio (perf)

| Algorithm | x86 cmiss% | ARM cmiss% |
|---|---:|---:|
| AES-256-CBC | TBD | TBD |
| SHA256 | TBD | TBD |
| ChaCha20 | TBD | TBD |

## 5. Branch miss ratio (perf)

| Algorithm | x86 bmiss% | ARM bmiss% |
|---|---:|---:|
| AES-256-CBC | TBD | TBD |
| SHA256 | TBD | TBD |
| ChaCha20 | TBD | TBD |

## 6. Crypto acceleration usage (opcode counts)

### x86 (Pin)

| Algorithm | AESENC | AESENCLAST | SHA256RNDS2 | SHA256MSG1 | SHA256MSG2 |
|---|---:|---:|---:|---:|---:|
| AES | TBD | TBD | 0 | 0 | 0 |
| SHA256 | 0 | 0 | TBD | TBD | TBD |
| ChaCha20 | 0 | 0 | 0 | 0 | 0 |

### ARM (DynamoRIO)

| Algorithm | AESE | AESMC | SHA256H | SHA256H2 | SHA256SU0 | SHA256SU1 |
|---|---:|---:|---:|---:|---:|---:|
| AES | TBD | TBD | 0 | 0 | 0 | 0 |
| SHA256 | 0 | 0 | TBD | TBD | TBD | TBD |
| ChaCha20 | 0 | 0 | 0 | 0 | 0 | 0 |

## 7. Unified cross-architecture CSV

The unified CSV (`results/comparison/unified_comparison.csv`) already supports an `architecture` column. After ARM runs are added, the file will have:

```
algorithm,architecture,perf_instructions,pin_instructions,dynamorio_instructions,...
AES,x86,537137518,529249390,528194004,...
AES,arm,TBD,TBD,TBD,...
```

## 8. Cross-architecture interpretation

- **AES**: x86 uses AESENC+AESENCLAST (1.33 IPC on Ryzen 5 7535HS). ARM uses AESE+AESMC. Compare cycles per byte and IPC to see which microarchitecture is more efficient.
- **SHA256**: x86 uses SHA256RNDS2+SHA256MSG1+SHA256MSG2. ARM uses SHA256H+SHA256H2+SHA256SU0+SHA256SU1. Note that ARM SHA-256 has more distinct opcodes (4 vs 3), which can affect dispatch and ILP.
- **ChaCha20**: no hardware acceleration on either. Compare pure software throughput. ARM's wider NEON/ASIMD registers may provide a relative speedup depending on compiler vectorization.

## 9. Sources of differences to investigate

1. AESENC vs AESE: different number of micro-ops per round.
2. SHA-NI dispatch paths: x86 has 3 opcodes; ARM has 4.
3. Branch predictor accuracy: differs by microarchitecture.
4. Cache hierarchy: L1D size, line size, associativity.
5. Memory ordering model: x86 strong, ARM weaker; affects write counts.

## 10. Required scripts to fill these tables

- `scripts/run_arm_perf.sh` (already prepared)
- `scripts/run_arm_dynamorio.sh` (already prepared)
- An updated `scripts/compare_unified.py` that accepts an `architecture` parameter and appends rows to `unified_comparison.csv`.

## 11. Acceptance criteria

- All TBDs are replaced by real measured values.
- Three full runs per host, with the median reported.
- A `docs/x86_vs_arm_report.md` is produced containing all tables and a one-paragraph interpretation per algorithm.
