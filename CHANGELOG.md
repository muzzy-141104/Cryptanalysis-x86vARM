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

ARM profiling implementation. To be populated once AWS Graviton instance is available. AWS Graviton setup documentation, ARM metrics spec, and ARM automation scripts are checked into `main` as a stable preparation layer.
