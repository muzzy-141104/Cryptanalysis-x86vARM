# DynamoRIO Setup and Usage

## Installation (Ubuntu 24.04)

1. Download DynamoRIO Linux x86_64 package from the official release page.
2. Extract it to a stable path, for example:

```bash
mkdir -p "$HOME/tools"
tar -xzf DynamoRIO-Linux-*.tar.gz -C "$HOME/tools"
```

3. Set environment variables (adjust versioned folder name):

```bash
export DYNAMORIO_HOME="$HOME/tools/DynamoRIO-Linux-<version>"
export PATH="$DYNAMORIO_HOME/bin64:$PATH"
```

4. Verify:

```bash
drrun -version
```

## Build Commands

Build the DynamoRIO client from project root:

```bash
gcc -shared -fPIC -O2 \
  -I"$DYNAMORIO_HOME/include" \
  dynamorio_client/dr_crypto_profiler.c \
  -o dynamorio_client/libdr_crypto_profiler.so \
  -L"$DYNAMORIO_HOME/lib64/release" -ldr_api -ldrmanager
```

If your package uses a different library directory, use `lib64/debug` or another available variant.

## Run Commands

Run with output path as client argument:

```bash
drrun -c dynamorio_client/libdr_crypto_profiler.so results/x86/dr_aes_profile.csv -- ./build/aes_driver 1048576 100
drrun -c dynamorio_client/libdr_crypto_profiler.so results/x86/dr_sha256_profile.csv -- ./build/sha256_driver 1048576 100
drrun -c dynamorio_client/libdr_crypto_profiler.so results/x86/dr_chacha20_profile.csv -- ./build/chacha20_driver 1048576 100
```

## Output Schema

Client output is Pin-compatible CSV:

```csv
metric,value
instruction_count,123456
memory_reads,45678
memory_writes,9876
```

## Client Architecture

`dynamorio_client/dr_crypto_profiler.c` structure:

1. **Global counters**: `instruction_count`, `memory_reads`, `memory_writes`.
2. **Instruction instrumentation callback**:
   - instruments each application instruction,
   - inspects src operands for memory reads,
   - inspects dst operands for memory writes,
   - inserts a clean call carrying per-instruction read/write counts.
3. **Thread-safe counter update**:
   - clean call updates global counters under a mutex.
4. **Exit callback**:
   - writes CSV file in Pin-compatible format.
5. **Configurable output path**:
   - default `results/arm/profile.csv`,
   - override via first client argument passed to `-c`.
