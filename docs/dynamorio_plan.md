# DynamoRIO Integration Plan (Design Only)

## Scope

This document defines the Phase 4 design for adding DynamoRIO-based profiling with CSV output compatible with the current Intel Pin pipeline. This is a planning document only; no DynamoRIO client is implemented here.

## 1) Installation Steps (Ubuntu 24.04)

1. Download the latest DynamoRIO Linux package from the official releases page.
2. Extract to a stable tools location (example: `~/tools/dynamorio`).
3. Export environment variables:
   - `DYNAMORIO_HOME=~/tools/dynamorio`
   - Add `$DYNAMORIO_HOME/bin64` to `PATH`.
4. Verify installation:
   - `drrun -version`
5. Validate with a smoke test:
   - `drrun -- /bin/true`

Optional build dependencies (for client compilation):

- `build-essential`
- `cmake`
- `python3`

## 2) Client Architecture

Planned source location:

- `dynamorio_client/crypto_profiler.cpp`

High-level components:

1. **Initialization**
   - Parse output path option (default `results/x86/profile.csv` or `results/arm/profile.csv`).
   - Initialize global counters.

2. **Instruction Event Hook**
   - Register a basic-block or instruction instrumentation callback.
   - Increment `instruction_count` per executed instruction.

3. **Memory Operand Analysis**
   - Inspect each instruction for source/destination memory operands.
   - Increment `memory_reads` and `memory_writes` based on decoded operand access.

4. **Opcode Classification (x86 first)**
   - Detect AES-NI opcodes: AESENC, AESDEC, AESENCLAST, AESDECLAST.
   - Detect SHA-NI opcodes: SHA256RNDS2, SHA256MSG1, SHA256MSG2.
   - Increment corresponding counters.

5. **Finalization**
   - Flush all counters to CSV with schema-compatible rows.

## 3) Equivalent Instruction Counting

Implementation intent:

- Instrument every application instruction in DynamoRIO.
- Use lightweight inline clean calls or counter updates depending on performance constraints.
- Ensure thread-safe updates:
  - Preferred: per-thread counters + merge at exit.
  - Acceptable initial approach: atomic global counters.

Target metric parity with Pin:

- `instruction_count`

## 4) Equivalent Memory Access Tracking

Implementation intent:

- For each instrumented instruction, inspect memory source and destination operands.
- Count each distinct read operand toward `memory_reads`.
- Count each distinct write operand toward `memory_writes`.

Edge cases to account for:

- Instructions with multiple memory reads.
- Read-modify-write instructions (increment both read and write counts).
- String/rep instructions where dynamic counts can be large.

Target metric parity with Pin:

- `memory_reads`
- `memory_writes`

## 5) CSV Compatibility Requirements

The DynamoRIO output must match the existing schema used by analysis scripts.

Output file format:

```csv
metric,value
instruction_count,123
memory_reads,45
memory_writes,67
aesenc_count,0
aesenclast_count,0
sha256rnds2_count,0
sha256msg1_count,0
sha256msg2_count,0
```

Compatibility rules:

1. First row must be exactly `metric,value`.
2. Metric names must exactly match script expectations.
3. Missing unsupported metrics must be emitted as `0` to keep consistent columns downstream.
4. Use integer values only.
5. Keep output location configurable via runtime option.

## 6) Verification Strategy

1. Run the same benchmark drivers under Pin and DynamoRIO with fixed input size/iterations.
2. Compare CSV structure and metric completeness.
3. Aggregate results with `scripts/aggregate_results.py` without code changes.
4. Validate chart and report generation with combined x86/arm paths in later phase.

## 7) Deferred Items (Not in this phase)

- ARM opcode mapping finalization
- Cross-architecture normalization strategy
- Performance overhead minimization
- CI/CD automation for DynamoRIO builds
