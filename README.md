# Cryptanalysis-x86vARM

Cross-Platform Cryptographic Behavior Analysis: x86 instrumentation (Intel Pin + DynamoRIO + perf) with ARM profiling preparation (AWS Graviton).

## Repository Structure

```
main
└── Stable x86 implementation
    ├── Pin profiler (AES-NI + SHA-NI)
    ├── DynamoRIO profiler (BB-aggregated)
    ├── perf hardware-counter pipeline
    ├── Unified comparison
    ├── Charts and report
    └── Cross-architecture design (docs only)

arm-analysis
└── ARM profiling work
    ├── AWS Graviton setup doc
    ├── ARM metrics spec
    ├── ARM automation scripts
    └── Cross-architecture comparison design
```

See branch-specific READMEs and the full x86 pipeline under `stable-x86` and the ARM-prep layer under `arm-analysis`.
