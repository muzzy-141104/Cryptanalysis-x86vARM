# Final Deliverables Index

## Reports

| File | Description |
|---|---|
| `docs/final_report.md` | Main academic report covering all phases |
| `docs/perf_analysis.md` | Hardware-counter interpretation |
| `docs/dynamorio_validation.md` | Pin vs DynamoRIO parity analysis |
| `docs/dynamorio_setup.md` | DynamoRIO installation and run guide |
| `docs/dynamorio_plan.md` | Phase 4 design plan |
| `docs/pin_vs_dynamorio.md` | Conceptual comparison of the two DBI frameworks |
| `docs/reproducibility.md` | Exact commands, environment, validation |
| `docs/results_appendix.md` | All tables, chart descriptions, observations |
| `results/x86/report.md` | Auto-generated x86 profile report |
| `docs/deliverables.md` | This file |

## Charts (PNG)

| File | Description |
|---|---|
| `charts/instruction_count.png` | Instruction counts per algorithm (Phase 2) |
| `charts/memory_reads.png` | Memory reads per algorithm (Phase 2) |
| `charts/memory_writes.png` | Memory writes per algorithm (Phase 2) |
| `charts/aes_opcode_usage.png` | AESENC + AESENCLAST per algorithm (Phase 2) |
| `charts/sha_opcode_usage.png` | SHA-NI opcode total per algorithm (Phase 2) |
| `charts/instructions_compare.png` | Pin vs DynamoRIO vs perf instruction counts (Phase 7) |
| `charts/ipc_compare.png` | IPC per algorithm (Phase 7) |
| `charts/cycles_compare.png` | CPU cycles per algorithm (Phase 7) |
| `charts/branch_miss_ratio.png` | Branch miss rate per algorithm (Phase 7) |
| `charts/cache_miss_ratio.png` | Cache miss rate per algorithm (Phase 7) |
| `charts/aes_ni_usage.png` | AESENC vs AESENCLAST stacked (Phase 7) |
| `charts/sha_ni_usage.png` | SHA-NI opcode counts (Phase 7) |

## CSV Data Files

### Pin per-algorithm

- `results/x86/aes_profile.csv`
- `results/x86/sha256_profile.csv`
- `results/x86/chacha20_profile.csv`

### Pin aggregated

- `results/x86/summary.csv`

### DynamoRIO per-algorithm

- `results/x86/dr_aes_profile.csv`
- `results/x86/dr_sha256_profile.csv`
- `results/x86/dr_chacha20_profile.csv`

### Pin vs DynamoRIO comparison

- `results/comparison/pin_vs_dynamorio.csv`

### perf per-algorithm

- `results/perf/aes_perf.csv`
- `results/perf/sha256_perf.csv`
- `results/perf/chacha20_perf.csv`

### perf summary

- `results/perf/perf_summary.csv`

### Unified comparison (all backends)

- `results/comparison/unified_comparison.csv`

## Diagrams (PNG + SVG)

| File | Description |
|---|---|
| `docs/diagrams/system_architecture.png` | Overall system architecture |
| `docs/diagrams/intel_pin_pipeline.png` | Intel Pin profiling pipeline |
| `docs/diagrams/dynamorio_pipeline.png` | DynamoRIO profiling pipeline |
| `docs/diagrams/perf_pipeline.png` | Linux perf pipeline |
| `docs/diagrams/unified_analysis_pipeline.png` | Cross-tool analysis pipeline |

Each diagram is also available as `.svg` in the same directory.

## Scripts

| File | Purpose |
|---|---|
| `scripts/aggregate_results.py` | Build `summary.csv` from per-algorithm Pin CSVs |
| `scripts/compare_pin_dynamorio.py` | Build Pin vs DynamoRIO comparison CSV |
| `scripts/compare_unified.py` | Merge perf, Pin, DynamoRIO, opcode counts |
| `scripts/parse_perf_csv.py` | Build `perf_summary.csv`; fails on zeros |
| `scripts/parse_perf_log.py` | Convert `perf stat` text output to CSV |
| `scripts/generate_charts.py` | Phase 2 charts (instructions, memory, opcodes) |
| `scripts/generate_perf_charts.py` | Phase 7 charts (perf + cross-tool) |
| `scripts/generate_report.py` | Generate `results/x86/report.md` |
| `scripts/generate_diagrams.py` | Generate architecture diagrams (PNG + SVG) |
| `scripts/run_x86_profile.sh` | Run Pin pipeline |
| `scripts/run_perf.sh` | Run perf pipeline |
| `scripts/run_all.sh` | One-command full reproduction |
| `scripts/open_charts.sh` | Open all charts in default viewer |

## Source Code

- `drivers/aes_driver.c`
- `drivers/sha256_driver.c`
- `drivers/chacha20_driver.c`
- `pin_tool/crypto_profiler.cpp`
- `pin_tool/makefile.rules`
- `dynamorio_client/dr_crypto_profiler.c`
- `dynamorio_client/libdr_crypto_profiler.so` (build artifact)
