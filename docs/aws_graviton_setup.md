# AWS Graviton ARM Setup (Phase 9 / Phase 9.1)

This document replaces the previous Oracle Cloud ARM references with AWS Graviton provisioning. Existing x86 documentation is preserved and remains the primary source for the laptop pipeline.

## 1. AWS EC2 Instance Configuration

- Region: `us-east-1` (or any region that offers Graviton; Graviton2 is available in all commercial regions)
- AMI: Ubuntu Server 24.04 LTS (ARM64)
  - Search for: "ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-arm64-server-*"
- Instance type: `t4g.medium`
  - 2 vCPUs (Graviton2)
  - 4 GB RAM
  - Free-tier eligible for 750 hours/month during the first 12 months
- Storage: 30 GB gp3 root volume (default is fine)
- Key pair: create or import an SSH key pair
- IAM: no special role required

### Security Group Requirements

| Type | Protocol | Port | Source | Purpose |
|---|---|---|---|---|
| SSH | TCP | 22 | Your IP / 32 | Operator access |

Outbound: default (allow all). No inbound ports other than SSH are required.

## 2. SSH Setup

```bash
chmod 600 ~/Downloads/graviton-key.pem
ssh -i ~/Downloads/graviton-key.pem ubuntu@<EC2_PUBLIC_IP>
```

For long-running profiling, use tmux or screen:

```bash
sudo apt install -y tmux
tmux new -s arm
```

To copy the project to the Graviton instance:

```bash
rsync -avz -e "ssh -i ~/Downloads/graviton-key.pem" \
  ~/projects/crypto-analysis/ ubuntu@<EC2_PUBLIC_IP>:~/crypto-analysis/
```

## 3. Validation Commands

After SSH-ing in:

```bash
uname -m
# expected: aarch64

lscpu
# expected: Architecture: aarch64, CPU(s): 2, Model name: Neoverse-N1

cat /proc/cpuinfo | grep Features
# expected to include: aes, sha1, sha2, asimd, cpuid, evtstrm, ...
```

Sanity check the OpenSSL backend:

```bash
openssl speed -evp aes-256-cbc -seconds 1
openssl speed -evp sha256 -seconds 1
openssl speed -evp chacha20 -seconds 1
```

## 4. Expected ARM Crypto Features

The `t4g.medium` instance exposes:

- `aes` — ARMv8 AES extension
- `sha1`, `sha2` — ARMv8 SHA-1 and SHA-256 extensions
- `asimd` — Advanced SIMD (NEON)
- `crc32`, `atomics`, `fp`, `asimdrdm`, `lrcpc`, `dcpop`

OpenSSL 3.x automatically dispatches to `aes` and `sha2` when these features are present.

## 5. DynamoRIO Installation Steps

```bash
# On the Graviton instance
cd ~
wget https://github.com/DynamoRIO/dynamorio/releases/download/<release>/DynamoRIO-Linux-AArch64-<release>.tar.gz
mkdir -p tools
tar -xzf DynamoRIO-Linux-AArch64-<release>.tar.gz -C tools
mv tools/DynamoRIO-Linux-AArch64-<release> tools/DynamoRIO
export DYNAMORIO_HOME=$HOME/tools/DynamoRIO
export PATH=$DYNAMORIO_HOME/bin64:$PATH
drrun -version
```

Expected output: a DynamoRIO version banner with `AArch64` in the platform line.

## 6. Build Instructions for crypto-analysis

```bash
git clone <repo-url> crypto-analysis
cd crypto-analysis
./scripts/setup_arm_env.sh
./scripts/build_arm_drivers.sh

# Build the DynamoRIO client for aarch64
gcc -shared -fPIC -O2 -DLINUX -DARM_64 -DUNIX \
  -I"$DYNAMORIO_HOME/include" -I"$DYNAMORIO_HOME/ext/include" \
  dynamorio_client/dr_crypto_profiler.c \
  -o dynamorio_client/libdr_crypto_profiler.so \
  -L"$DYNAMORIO_HOME/lib64/release" -L"$DYNAMORIO_HOME/ext/lib64/release" \
  -ldrmgr -ldynamorio -lpthread

# Python environment
python3 -m venv .venv
.venv/bin/pip install pandas matplotlib
```

## 7. ARM Profiling Workflow

### perf

```bash
sudo sysctl -w kernel.perf_event_paranoid=1
./scripts/run_arm_perf.sh
```

This populates `results/arm/{aes,sha256,chacha20}_perf.csv` and `results/arm/perf_summary.csv`.

### DynamoRIO

```bash
export CLIENT_SO=$PWD/dynamorio_client/libdr_crypto_profiler.so
./scripts/run_arm_dynamorio.sh
```

This populates `results/arm/{aes,sha256,chacha20}_profile.csv`.

### Report Generation

Once both perf and DynamoRIO CSVs are in place, the existing x86 analysis pipeline can be reused with path overrides:

```bash
PYTHON_BIN=./.venv/bin/python \
  ./scripts/run_all.sh
```

Or, on the ARM host, copy the ARM CSVs into `results/x86/` (after locally renaming the file format if needed) and run the existing aggregation scripts.

## 8. x86 vs ARM Comparison Methodology

1. Run identical drivers and identical workload (`<binary> 1048576 100`) on both hosts.
2. Capture DynamoRIO and perf metrics on each host.
3. Merge results into `results/comparison/unified_comparison.csv` using an `architecture` column.
4. Compute, per algorithm:
   - Throughput ratio (x86 / ARM)
   - Instructions-per-byte ratio
   - Cycles-per-byte ratio
   - IPC ratio
   - Branch-miss and cache-miss ratios
5. Compare crypto-opcode usage:
   - x86: AESENC, AESENCLAST, SHA256RNDS2, SHA256MSG1, SHA256MSG2
   - ARM: AESE, AESMC, SHA256H, SHA256H2, SHA256SU0, SHA256SU1
6. Three runs per host; report the median.
7. Document the comparison in `docs/x86_vs_arm_design.md` (replace the TBD rows with measured values) and add a new `docs/x86_vs_arm_report.md` summarizing the findings.

## 9. Cost / Quota Notes

- `t4g.medium` is free-tier eligible for 12 months (750 hours/month).
- Stop the instance when not in use to avoid waste.
- After free-tier expires, on-demand t4g pricing is around $0.0332/hour.
- No ARM capacity quotas comparable to Oracle's Ampere A1 limits.

## 10. Tear Down

```bash
# Stop the instance to release compute
aws ec2 stop-instances --instance-ids <INSTANCE_ID>

# Or terminate when finished
aws ec2 terminate-instances --instance-ids <INSTANCE_ID>
```
