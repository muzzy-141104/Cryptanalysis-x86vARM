# Algorithms Used for Testing

## Overview

The project performs **cross-architecture cryptographic behavior analysis** comparing x86_64 and ARMv8 using three measurement backends: Intel Pin, DynamoRIO, and Linux `perf`.

---

## Algorithms Tested

| # | Algorithm | Full Name | OpenSSL API | Source File |
|---|-----------|-----------|-------------|-------------|
| 1 | **AES-256-CBC** | Advanced Encryption Standard, 256-bit key, CBC mode | `EVP_aes_256_cbc()` | `drivers/aes_driver.c` |
| 2 | **SHA-256** | Secure Hash Algorithm, 256-bit digest | `EVP_sha256()` | `drivers/sha256_driver.c` |
| 3 | **ChaCha20** | ChaCha20 stream cipher | `EVP_chacha20()` | `drivers/chacha20_driver.c` |

---

## How Values Are Passed (End-to-End Flow)

### Step 1: Shell Scripts Define Defaults via Environment Variables

All shell scripts use the same pattern with bash parameter expansion to set defaults:

```bash
DATA_SIZE="${DATA_SIZE:-1048576}"   # 1 MB default
ITERATIONS="${ITERATIONS:-100}"     # 100 iterations default
```

**Files that define these defaults:**

| Script | Line | Variable |
|--------|------|----------|
| `scripts/run_all.sh` | 12 | `DATA_SIZE="${DATA_SIZE:-1048576}"` |
| `scripts/run_all.sh` | 13 | `ITERATIONS="${ITERATIONS:-100}"` |
| `scripts/run_perf.sh` | 8 | `DATA_SIZE="${DATA_SIZE:-1048576}"` |
| `scripts/run_perf.sh` | 9 | `ITERATIONS="${ITERATIONS:-100}"` |
| `scripts/run_x86_profile.sh` | 10 | `DATA_SIZE="${DATA_SIZE:-1048576}"` |
| `scripts/run_x86_profile.sh` | 11 | `ITERATIONS="${ITERATIONS:-100}"` |
| `scripts/run_arm_perf.sh` | 12 | `DATA_SIZE="${DATA_SIZE:-1048576}"` |
| `scripts/run_arm_perf.sh` | 13 | `ITERATIONS="${ITERATIONS:-100}"` |
| `scripts/run_arm_dynamorio.sh` | 12 | `DATA_SIZE="${DATA_SIZE:-1048576}"` |
| `scripts/run_arm_dynamorio.sh` | 13 | `ITERATIONS="${ITERATIONS:-100}"` |

**Override example:**
```bash
DATA_SIZE=2097152 ITERATIONS=200 ./scripts/run_all.sh
```

---

### Step 2: Scripts Pass Values to Driver Binaries via CLI Arguments

All three drivers use the **identical interface**:

```
Usage: <binary> <data_size_bytes> <iterations>
```

The scripts pass `$DATA_SIZE` and `$ITERATIONS` as positional arguments:

**Pin profiling** (`scripts/run_x86_profile.sh:51-57`):
```bash
$PIN_BIN -t $PIN_TOOL_SO -o results/x86/aes_profile.csv -- ./build/aes_driver "$DATA_SIZE" "$ITERATIONS"
$PIN_BIN -t $PIN_TOOL_SO -o results/x86/sha256_profile.csv -- ./build/sha256_driver "$DATA_SIZE" "$ITERATIONS"
$PIN_BIN -t $PIN_TOOL_SO -o results/x86/chacha20_profile.csv -- ./build/chacha20_driver "$DATA_SIZE" "$ITERATIONS"
```

**DynamoRIO profiling** (`scripts/run_arm_dynamorio.sh:46-48`):
```bash
$DYNAMORIO_BIN -c $CLIENT_SO $out_csv -- ./build/aes_driver "$DATA_SIZE" "$ITERATIONS"
$DYNAMORIO_BIN -c $CLIENT_SO $out_csv -- ./build/sha256_driver "$DATA_SIZE" "$ITERATIONS"
$DYNAMORIO_BIN -c $CLIENT_SO $out_csv -- ./build/chacha20_driver "$DATA_SIZE" "$ITERATIONS"
```

**perf profiling** (`scripts/run_perf.sh:51-54`):
```bash
perf stat -e "$EVENTS" -o $perf_log ./build/aes_driver "$DATA_SIZE" "$ITERATIONS"
perf stat -e "$EVENTS" -o $perf_log ./build/sha256_driver "$DATA_SIZE" "$ITERATIONS"
perf stat -e "$EVENTS" -o $perf_log ./build/chacha20_driver "$DATA_SIZE" "$ITERATIONS"
```

---

### Step 3: Driver Binaries Parse CLI Arguments via `argv`

Each driver's `main()` function parses the two positional arguments:

**AES driver** (`drivers/aes_driver.c:18-19`):
```c
size_t data_size = strtoull(argv[1], NULL, 10);
int iterations = atoi(argv[2]);
```

**SHA-256 driver** (`drivers/sha256_driver.c:15-16`):
```c
size_t data_size = strtoull(argv[1], NULL, 10);
int iterations = atoi(argv[2]);
```

**ChaCha20 driver** (`drivers/chacha20_driver.c:18-19`):
```c
size_t data_size = strtoull(argv[1], NULL, 10);
int iterations = atoi(argv[2]);
```

All three validate argc == 3 and print usage if wrong:
```c
if (argc != 3) {
    printf("Usage: %s <data_size_bytes> <iterations>\n", argv[0]);
    return 1;
}
```

---

### Step 4: Hardcoded Cryptographic Parameters in C Source

These values are **not passed via arguments** -- they are hardcoded as global static variables:

**AES-256-CBC** (`drivers/aes_driver.c:7-8`):
```c
static unsigned char key[32] = {0};   // 32 bytes, all zeros
static unsigned char iv[16] = {0};    // 16 bytes, all zeros
```

**ChaCha20** (`drivers/chacha20_driver.c:7-8`):
```c
static unsigned char key[32] = {0};    // 32 bytes, all zeros
static unsigned char nonce[16] = {0};  // 16 bytes, all zeros
```

**SHA-256** has no key/IV -- it is a hash function.

**Plaintext/input fill** (all three drivers):
```c
memset(plaintext, 'A', data_size);  // Fill buffer with 'A' (0x41)
```
- AES: `drivers/aes_driver.c:30`
- SHA-256: `drivers/sha256_driver.c:34`
- ChaCha20: `drivers/chacha20_driver.c:38`

---

### Step 5: Values Flow into OpenSSL API Calls

**AES-256-CBC** (`drivers/aes_driver.c:43-49`):
```c
EVP_EncryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv);
EVP_EncryptUpdate(ctx, ciphertext, &len, plaintext, data_size);
EVP_EncryptFinal_ex(ctx, ciphertext + ciphertext_len, &len);
```
- `key` and `iv` come from hardcoded globals
- `data_size` comes from `argv[1]`
- Loop runs `iterations` times (from `argv[2]`)

**SHA-256** (`drivers/sha256_driver.c:51-53`):
```c
EVP_DigestInit_ex(ctx, EVP_sha256(), NULL);
EVP_DigestUpdate(ctx, input, data_size);
EVP_DigestFinal_ex(ctx, digest, &digest_len);
```
- `data_size` comes from `argv[1]`
- Loop runs `iterations` times (from `argv[2]`)

**ChaCha20** (`drivers/chacha20_driver.c:58-59`):
```c
EVP_EncryptInit_ex(ctx, EVP_chacha20(), NULL, key, nonce);
EVP_EncryptUpdate(ctx, ciphertext, &len, plaintext, data_size);
```
- `key` and `nonce` come from hardcoded globals
- `data_size` comes from `argv[1]`
- Loop runs `iterations` times (from `argv[2]`)
- No `EVP_EncryptFinal_ex` needed (stream cipher)

---

### Step 6: Instrumentation Tools Intercept Driver Execution

**Intel Pin** wraps the driver binary:
```bash
$PIN_BIN -t $PIN_TOOL_SO -o results/x86/aes_profile.csv -- ./build/aes_driver $DATA_SIZE $ITERATIONS
```
- `-t` : path to Pin tool shared object
- `-o` : output CSV path
- `--` : separator before target binary + its arguments

**DynamoRIO** wraps the driver binary:
```bash
$DYNAMORIO_BIN -c $CLIENT_SO results/arm/dr_aes_profile.csv -- ./build/aes_driver $DATA_SIZE $ITERATIONS
```
- `-c` : client shared library path
- Positional arg after client : output CSV path
- `--` : separator before target binary + its arguments

**Linux perf** wraps the driver binary:
```bash
perf stat -e "cpu-cycles,instructions,..." -o logs/perf/aes_perf.log ./build/aes_driver $DATA_SIZE $ITERATIONS
```
- `-e` : comma-separated perf event list
- `-o` : output log file path

---

## Summary: Complete Parameter Flow Diagram

```
User runs:
  DATA_SIZE=1048576 ITERATIONS=100 ./scripts/run_all.sh

  ┌─────────────────────────────────────────────────┐
  │  Shell Script (run_all.sh)                       │
  │  DATA_SIZE="${DATA_SIZE:-1048576}"  ← env var    │
  │  ITERATIONS="${ITERATIONS:-100}"    ← env var    │
  └──────────────────────┬──────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
  ┌──────────┐   ┌──────────┐   ┌──────────┐
  │ Pin Tool │   │ DynamoRIO│   │  perf    │
  │ -t ...   │   │ -c ...   │   │ -e ...   │
  │ -o ...   │   │ -o ...   │   │ -o ...   │
  └────┬─────┘   └────┬─────┘   └────┬─────┘
       │              │              │
       └──────────────┼──────────────┘
                      ▼
  ┌─────────────────────────────────────────────────┐
  │  Driver Binary (e.g. aes_driver)                │
  │  ./build/aes_driver 1048576 100                 │
  │                                                  │
  │  argv[1] = "1048576"  → strtoull → data_size   │
  │  argv[2] = "100"      → atoi     → iterations  │
  │                                                  │
  │  key[32] = {0}   ← hardcoded global             │
  │  iv[16]  = {0}   ← hardcoded global             │
  │  memset(plaintext, 'A', data_size)  ← hardcoded │
  └──────────────────────┬──────────────────────────┘
                         │
                         ▼
  ┌─────────────────────────────────────────────────┐
  │  OpenSSL API Calls                               │
  │  EVP_EncryptInit_ex(ctx, EVP_aes_256_cbc(),      │
  │                     NULL, key, iv)               │
  │  EVP_EncryptUpdate(ctx, out, &len,               │
  │                    plaintext, data_size)          │
  │  EVP_EncryptFinal_ex(ctx, out + len, &len)       │
  │                                                  │
  │  Repeated `iterations` times                     │
  └─────────────────────────────────────────────────┘
```

---

## Algorithm Parameters Summary Table

| Algorithm | Key/IV | Data Size | Iterations | Input Fill | OpenSSL API |
|-----------|--------|-----------|------------|------------|-------------|
| AES-256-CBC | 32B key (zeros) + 16B IV (zeros) | 1,048,576 B (1 MB) | 100 | `'A'` repeated | `EVP_aes_256_cbc()` |
| SHA-256 | N/A | 1,048,576 B (1 MB) | 100 | `'A'` repeated | `EVP_sha256()` |
| ChaCha20 | 32B key (zeros) + 16B nonce (zeros) | 1,048,576 B (1 MB) | 100 | `'A'` repeated | `EVP_chacha20()` |

---

## Parameter Passing Mechanisms Summary

| Mechanism | Parameters | Example |
|-----------|-----------|---------|
| **CLI arguments** | `data_size`, `iterations` | `./build/aes_driver 1048576 100` |
| **Environment variables** | `DATA_SIZE`, `ITERATIONS` | `DATA_SIZE=2097152 ./scripts/run_all.sh` |
| **Hardcoded in C** | key, IV/nonce, fill char | `static unsigned char key[32] = {0}` |
| **Hardcoded in scripts** | default values, perf events | `DATA_SIZE="${DATA_SIZE:-1048576}"` |
| **Pin flags** | `-t`, `-o` | `-t pin_tool.so -o results/x86/aes.csv` |
| **DynamoRIO flags** | `-c` | `-c libdr_crypto_profiler.so results/arm/dr.csv` |
| **perf flags** | `-e`, `-o` | `-e cpu-cycles,instructions -o log.txt` |

---

## Perf Events by Architecture

### x86 Events (`scripts/run_perf.sh:13-22`)
```
cpu-cycles, instructions, branch-instructions, branch-misses,
cache-references, cache-misses, stalled-cycles-frontend, stalled-cycles-backend
```

### ARM Events (`scripts/run_arm_perf.sh:18-29`)
```
cpu_cycles, inst_retired, br_retired, br_mis_pred_retired,
l1d_cache, l1d_cache_refill, l1i_cache, l1i_cache_refill,
stall_frontend, stall_backend
```

---

## Build Parameters

All drivers are compiled with (`scripts/run_all.sh:23-25`):
```bash
gcc drivers/aes_driver.c      -O2 -o build/aes_driver      -lcrypto
gcc drivers/sha256_driver.c   -O2 -o build/sha256_driver   -lcrypto
gcc drivers/chacha20_driver.c -O2 -o build/chacha20_driver -lcrypto
```
