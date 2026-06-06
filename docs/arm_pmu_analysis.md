# ARM PMU Discovery and Mapping (Graviton)

## Summary

On this AWS Graviton environment, the PMU unit exposed by `perf list` is `armv8_pmuv3_0`.
Generic Linux aliases like `branch-instructions`, `branch-misses`, `cache-references`, and
`cache-misses` may be unavailable or mapped inconsistently depending on kernel/perf build.
For repeatable ARM profiling, the pipeline now uses native PMUv3 event names.

## Discovery Output

- Script: `scripts/discover_arm_pmu.sh`
- Generated event inventory: `results/arm/available_pmu_events.txt`

The discovery script runs `perf list`, captures events annotated with
`Unit: armv8_pmuv3_0`, and writes a sorted list.

## x86 Alias vs ARM PMUv3 Mapping

| Analysis metric | Typical x86 alias | ARM PMUv3 event used |
|---|---|---|
| Instructions retired | `instructions` | `inst_retired` |
| Branch instructions | `branch-instructions` | `br_retired` |
| Branch misses | `branch-misses` | `br_mis_pred_retired` |
| L1D cache accesses | `cache-references` (often LLC on x86) | `l1d_cache` |
| L1D cache refills | `cache-misses` (often LLC misses on x86) | `l1d_cache_refill` |
| L1I cache accesses | N/A (no generic alias) | `l1i_cache` |
| L1I cache refills | N/A (no generic alias) | `l1i_cache_refill` |

Additional ARM-native stall counters now used:

- `stall_frontend`
- `stall_backend`

## Validation

Each required ARM event was validated with:

```bash
perf stat -e <event> -- sleep 0.1
```

Validation matrix is in `results/arm/pmu_validation.csv`.

## Pipeline Changes

Updated script:

- `scripts/run_arm_perf.sh`

ARM perf collection now requests native events:

- `cpu_cycles`
- `inst_retired`
- `br_retired`
- `br_mis_pred_retired`
- `l1d_cache`
- `l1d_cache_refill`
- `l1i_cache`
- `l1i_cache_refill`
- `stall_frontend`
- `stall_backend`

To preserve existing downstream schema (`cpu-cycles`, `instructions`,
`branch-instructions`, etc.), `scripts/parse_perf_log.py` now maps ARM-native names
to canonical column names via alias expansion.

## Practical Difference: x86 Aliases vs ARM PMUv3

- x86 generic aliases are usually stable abstractions over architectural and model-specific events.
- On ARM/Graviton, generic aliases can be absent or semantically different from the target metric.
- ARM PMUv3 names (`inst_retired`, `br_retired`, `l1d_cache_refill`, etc.) are explicit and
  directly tied to architected PMU definitions.
- Using PMUv3-native events reduces ambiguity and makes cross-run reproducibility better
  on ARM hosts.
