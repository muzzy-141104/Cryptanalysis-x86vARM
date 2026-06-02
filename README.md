# arm-analysis

ARM profiling work for the cross-architecture phase of the Cryptanalysis-x86vARM project.

## Status

In development. The stable x86 implementation lives on the `main` branch.

## Contents

- `docs/aws_graviton_setup.md` — AWS Graviton provisioning
- `docs/arm_metrics.md` — ARM AES/SHA extension opcode spec
- `docs/x86_vs_arm_design.md` — future comparison table templates
- `scripts/setup_arm_env.sh`
- `scripts/build_arm_drivers.sh`
- `scripts/run_arm_perf.sh`
- `scripts/run_arm_dynamorio.sh`

## Goal

When an AWS Graviton (t4g.medium) Ubuntu 24.04 aarch64 instance is available:

1. SSH in, run `scripts/setup_arm_env.sh`.
2. Build drivers with `scripts/build_arm_drivers.sh`.
3. Build the DynamoRIO AArch64 client.
4. Collect perf data with `scripts/run_arm_perf.sh`.
5. Collect DynamoRIO data with `scripts/run_arm_dynamorio.sh`.
6. Merge results into `results/comparison/unified_comparison.csv` with an `architecture` column.
7. Fill in the TBD rows of `docs/x86_vs_arm_design.md`.
8. Publish `docs/x86_vs_arm_report.md` as the final cross-architecture report.

## Architecture Targets

- AWS Graviton2 (Neoverse-N1)
- AES extension: AESE, AESD, AESMC, AESIMC
- SHA-256 extension: SHA256H, SHA256H2, SHA256SU0, SHA256SU1
- perf events: cpu_cycles, instructions, br_inst_retired, br_mis_pred, L1D_CACHE_REFILL
