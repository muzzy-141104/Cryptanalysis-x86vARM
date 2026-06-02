# x86 Cryptographic Behavior Report

## Methodology

Dynamic binary instrumentation is performed with Intel Pin on x86_64.
Per-run profiler output is collected as metric/value CSV files, then aggregated using pandas.
Visualization is generated with matplotlib and report sections are derived from summary statistics.

## Benchmark Configuration

- Algorithms: AES-256-CBC, SHA256, ChaCha20
- Driver interface: `<binary> <data_size_bytes> <iterations>`
- Typical workload: 1,048,576 bytes x 100 iterations
- Host architecture: x86_64

## Instruction Analysis

| algorithm | instruction_count |
| --- | --- |
| AES | 529249390 |
| SHA256 | 286776734 |
| ChaCha20 | 338676989 |

## Memory Analysis

| algorithm | memory_reads | memory_writes |
| --- | --- | --- |
| AES | 107067921 | 8688363 |
| SHA256 | 34270834 | 1834950 |
| ChaCha20 | 37828686 | 14618105 |

## AES-NI Analysis

| algorithm | aesenc_count | aesenclast_count |
| --- | --- | --- |
| AES | 85198100 | 6555000 |
| SHA256 | 0 | 0 |
| ChaCha20 | 0 | 0 |

## SHA-NI Analysis

| algorithm | sha256rnds2_count | sha256msg1_count | sha256msg2_count |
| --- | --- | --- | --- |
| AES | 0 | 0 | 0 |
| SHA256 | 52432000 | 19662000 | 19662000 |
| ChaCha20 | 0 | 0 | 0 |

## Observations

- Highest total instruction count: **AES**.
- Highest read/write ratio: **SHA256** (18.68).
- Most AES hardware-op activity observed in: **AES**.
- Most SHA hardware-op activity observed in: **SHA256**.
