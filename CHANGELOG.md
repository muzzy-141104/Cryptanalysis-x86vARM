# Changelog

## main (Stable x86 implementation)

Phase 1-8 complete. Validated cross-tool agreement.

### Drivers
- AES-256-CBC, SHA256, ChaCha20 benchmark drivers (`drivers/`) using OpenSSL EVP

### Intel Pin profiler (`pin_tool/crypto_profiler.cpp`)
- instruction_count, memory_reads, memory_writes counters
- AES-NI opcode detection: AESENC, AESDEC, AESENCLAST, AESDECLAST
- SHA-NI opcode detection: SHA256RNDS2, SHA256MSG1, SHA256MSG2
- Configurable output via -o knob; CSV schema in `results/x86/`

### DynamoRIO profiler (`dynamorio_client/dr_crypto_profiler.c`)
- Basic-block aggregation (one clean call per BB execution)
- instr_reads_memory / instr_writes_memory for memory classification
- Pin-compatible CSV schema
- Validated parity with Pin: instruction counts agree within 0.4% across all three algorithms

### perf hardware counter pipeline
- `scripts/run_perf.sh`, `scripts/parse_perf_log.py`, `scripts/parse_perf_csv.py`
- Captures cpu-cycles, instructions, branch-instructions, branch-misses, cache-references, cache-misses, stalled-cycles-frontend
- Validated non-zero instruction count (~537M for AES, ~290M for SHA256, ~348M for ChaCha20)
- Parser refuses to emit zero-valued summary

### Analysis layer
- `scripts/aggregate_results.py` -> `results/x86/summary.csv`
- `scripts/compare_pin_dynamorio.py` -> `results/comparison/pin_vs_dynamorio.csv`
- `scripts/compare_unified.py` -> `results/comparison/unified_comparison.csv`
- `scripts/generate_charts.py` + `scripts/generate_perf_charts.py` -> `charts/*.png`
- `scripts/generate_report.py` -> `results/x86/report.md`
- `scripts/generate_diagrams.py` -> `docs/diagrams/*.png` and `*.svg`

### Reports
- `docs/final_report.md` - main academic report
- `docs/results_appendix.md` - all tables and observations
- `docs/reproducibility.md` - exact commands and validation
- `docs/perf_analysis.md` - hardware counter interpretation
- `docs/dynamorio_validation.md` - Pin vs DynamoRIO parity analysis
- `docs/dynamorio_setup.md`, `docs/dynamorio_plan.md`, `docs/pin_vs_dynamorio.md`
- `docs/deliverables.md` - master index

### Cross-architecture preparation (docs only)
- `docs/x86_vs_arm_design.md` - future comparison table templates
- `docs/arm_metrics.md` - ARM AES/SHA extension opcode spec
- `docs/aws_graviton_setup.md` - AWS Graviton provisioning guide
- `docs/diagrams/cross_architecture_pipeline.png` and `.svg`

### ARM automation scripts (Phase 9 prep)
- `scripts/setup_arm_env.sh`
- `scripts/build_arm_drivers.sh`
- `scripts/run_arm_perf.sh`
- `scripts/run_arm_dynamorio.sh`

### End-to-end automation
- `scripts/run_all.sh` - one-command full reproduction
- `scripts/open_charts.sh` - open all generated charts

## arm-analysis

ARM profiling implementation. Pipeline complete.

### ARM PMU discovery
- `scripts/discover_arm_pmu.sh` -> `results/arm/available_pmu_events.txt` (90 events)
- `results/arm/pmu_validation.csv` records per-event validation

### ARM profiling pipeline
- `scripts/run_arm_perf.sh` now requests native `armv8_pmuv3_0` events:
  `cpu_cycles`, `inst_retired`, `br_retired`, `br_mis_pred_retired`,
  `l1d_cache`, `l1d_cache_refill`, `l1i_cache`, `l1i_cache_refill`,
  `stall_frontend`, `stall_backend`
- `scripts/parse_perf_log.py` aliases ARM-native names to the canonical
  schema (`instructions`, `branch-instructions`, etc.)
- `scripts/parse_perf_csv.py` no longer hard-fails on zero/missing PMU
  counters; it records them as `N/A` so summary generation completes in
  restricted PMU environments

### ARM analysis artifacts
- `results/arm/summary.csv` (throughput, execution_time, cycles,
  crypto_extensions_present)
- `results/arm/perf_summary.csv`
- `results/comparison/x86_vs_arm.csv` (x86 vs ARM throughput + cycles)
- `charts/x86_vs_arm_throughput.png`, `charts/x86_vs_arm_cycles.png`
- `docs/arm_pmu_analysis.md` (event mapping)
- `docs/arm_analysis.md` (Graviton + Neoverse-N1 + PMU limitation)

## Phase 8C - Final ARM Comparison

- Removed hard-fail logic from `scripts/parse_perf_csv.py`
- `results/arm/summary.csv`, `results/comparison/x86_vs_arm.csv` generated
- Comparison charts produced
- `docs/arm_analysis.md` and `docs/final_project_report.md` written
- Generator: `scripts/generate_arm_phase8c.py`

## Phase 9 - Dashboard

- `dashboard/backend/` FastAPI app exposing `/api/{overview,x86,arm,comparison,charts,reports}` and serving charts as static assets
- `dashboard/frontend/` Vite + React + Tailwind UI with pages:
  Overview, x86, ARM, Comparison, Charts, Report Viewer
- `dashboard/README.md` documents single-instance and SSH-port-forward setups
- All endpoints verified 200 against committed artifacts
