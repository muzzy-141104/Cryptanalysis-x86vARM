# ARM Cryptographic Behavior Report

## AWS Graviton Setup

The ARM profiling target is an AWS Graviton2 instance (`t4g.medium`) running
Ubuntu Server 24.04 LTS (ARM64). The provisioning steps, including security
group configuration, SSH access, OpenSSL sanity checks, and perf/DynamoRIO
installation, are documented in `docs/aws_graviton_setup.md`.

Validated host properties on Graviton:

- Architecture: `aarch64`
- CPU model: Neoverse-N1 (Graviton2)
- Crypto extensions exposed: `aes`, `sha1`, `sha2`
- OpenSSL: 3.x, automatic dispatch to ARMv8 AES/SHA extensions

## Neoverse-N1 Architecture

AWS Graviton2 uses the Arm Neoverse-N1 core. Key features relevant to this
study:

- ARMv8.2-A baseline
- Crypto extensions: AES, SHA-1, SHA-256
- 32 KB L1I and 32 KB L1D per core
- 1 MB L2 per core
- 4-way superscalar, out-of-order

PMU: `armv8_pmuv3_0` exposed via `perf list`. The full discovered event set is
captured in `results/arm/available_pmu_events.txt`.

## AES Support

The `aes` feature flag in `/proc/cpuinfo` enables the ARMv8 AES extension.
Relevant opcodes on AArch64:

- AESE (AES single round encryption)
- AESD (AES single round decryption)
- AESMC (AES mix columns)
- AESIMC (AES inverse mix columns)

OpenSSL automatically dispatches to these opcodes for AES-128/192/256-CBC
when the host advertises the `aes` extension. The `crypto_extensions_present`
column in `results/arm/summary.csv` reports `yes` for AES.

## SHA Support

The `sha2` feature flag enables the ARMv8 SHA-256 extension. Relevant opcodes:

- SHA256H
- SHA256H2
- SHA256SU0
- SHA256SU1

OpenSSL automatically dispatches to these opcodes for SHA-256. The
`crypto_extensions_present` column in `results/arm/summary.csv` reports `yes`
for SHA256.

ChaCha20 does not have a dedicated ARM crypto opcode and is implemented as a
pure software ARX pipeline; the column reports `no`.

## OpenSSL Verification

Sanity check using OpenSSL `speed` confirms that hardware-accelerated paths
are active on the Graviton host:

```bash
openssl speed -evp aes-256-cbc -seconds 1
openssl speed -evp sha256 -seconds 1
openssl speed -evp chacha20 -seconds 1
```

## Throughput Results

Throughput is derived from the driver-reported `clock_gettime(CLOCK_MONOTONIC)`
wall time, which is independent of the PMU access restrictions described
below. The aggregated ARM summary is at `results/arm/summary.csv`.

| Algorithm | Throughput (MB/s) | Execution Time (s) | Cycles | Crypto Extensions |
|---|---:|---:|---:|---|
| AES-256-CBC | 1213.31 | 0.0824 | 193,174,022 | yes |
| SHA256 | 1363.33 | 0.0734 | 171,299,291 | yes |
| ChaCha20 | 915.67 | 0.1092 | 255,996,062 | no |

## PMU Limitation Discussion

In this Graviton environment, the PMU events that require architectural
retired/cache/branch counters return zero values for user-space workloads,
even though `perf list` advertises the events and `perf stat -e <event>`
runs without error. Concretely:

- `cpu_cycles` and `task-clock` report non-zero values.
- `inst_retired`, `br_retired`, `br_mis_pred_retired`, `l1d_cache`,
  `l1d_cache_refill`, `l1i_cache`, `l1i_cache_refill`, `stall_frontend`, and
  `stall_backend` all report zero.

This is consistent with a virtualization/hypervisor restriction on PMU
counter access for non-privileged workloads. Validation per event is recorded
in `results/arm/pmu_validation.csv`.

To make the pipeline robust to this environment, the ARM perf summary uses
`N/A` for any counter that is not meaningful, instead of failing the
summary:

```
algorithm,cpu-cycles,instructions,branch-instructions,branch-misses,cache-references,cache-misses,stalled-cycles-frontend,stalled-cycles-backend,ipc,branch_miss_ratio,cache_miss_ratio
AES,193174022,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A
SHA256,171299291,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A
ChaCha20,255996062,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A
```

`cycles` (a software-visible monotonic counter) is still available and used
as the source of `arm_cycles` in the cross-architecture comparison.

## Summary

- ARM crypto extensions (AES, SHA-256) are exposed and used by OpenSSL.
- The ARM profile pipeline successfully captures wall-clock throughput and
  cycle counts on Graviton.
- Retired-instruction, branch, and cache PMU counters are not accessible
  to user space in this environment, so per-event PMU metrics are reported
  as `N/A` rather than zero.
- The cross-architecture comparison (`results/comparison/x86_vs_arm.csv`)
  is produced from the available measurements only.
