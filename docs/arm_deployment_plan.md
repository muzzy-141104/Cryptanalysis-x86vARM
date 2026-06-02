# ARM Deployment Plan (Phase 9 Preparation)

This document describes how to provision an Oracle Cloud ARM VM, prepare the Ubuntu ARM environment, install the required toolchain, and validate that DynamoRIO ARM profiling is available. No ARM execution is implemented in this phase; only the environment and automation layer are prepared.

## 1. Oracle Cloud ARM Setup

### Instance recommendation

- Shape: `VM.Standard.A1.Flex`
- vCPUs: 4 (ARM Ampere Altra)
- RAM: 24 GB
- Boot volume: 100 GB
- OS: Ubuntu 22.04 LTS or Ubuntu 24.04 LTS (aarch64)

Oracle Cloud's free tier offers up to 4 OCPUs and 24 GB RAM for Ampere A1 instances.

### Provisioning steps

1. Sign in to https://cloud.oracle.com/
2. Compute -> Instances -> Create Instance
3. Select "Ubuntu" as the image, aarch64 architecture
4. Choose `VM.Standard.A1.Flex` shape
5. Configure VCN, subnet, and public IP
6. Download the SSH key pair (.key file) from the console
7. Wait for the instance to reach RUNNING state
8. Note the public IP

## 2. Ubuntu ARM Installation

Oracle-provided Ubuntu ARM images ship with cloud-init. After first boot, update:

```bash
sudo apt update
sudo apt -y upgrade
```

Verify architecture:

```bash
uname -m
# expected: aarch64
```

## 3. SSH Access Workflow

```bash
chmod 600 ~/Downloads/oracle-arm.key
ssh -i ~/Downloads/oracle-arm.key ubuntu@<PUBLIC_IP>
```

For long-running sessions, use tmux:

```bash
sudo apt install -y tmux
tmux new -s arm
```

## 4. Required Packages

Captured in `scripts/setup_arm_env.sh`. Summary:

- build-essential (gcc, g++, make)
- cmake
- libssl-dev (OpenSSL headers and libraries)
- python3
- python3-venv
- linux-tools-generic (perf)

## 5. OpenSSL Installation

```bash
sudo apt install -y libssl-dev
openssl version
```

Expected: OpenSSL 3.0.x or newer.

## 6. perf Installation

```bash
sudo apt install -y linux-tools-generic linux-tools-common
perf --version
```

If `/proc/sys/kernel/perf_event_paranoid` is too restrictive:

```bash
sudo sysctl -w kernel.perf_event_paranoid=1
```

## 7. DynamoRIO ARM Support Validation

DynamoRIO supports ARM and AArch64. The ARM build is published in the same release as the x86 build, with separate binaries.

Validate on the ARM host:

```bash
uname -m
file /usr/bin/ls   # ELF 64-bit LSB executable, ARM aarch64
```

For DynamoRIO ARM downloads, see the official releases page under "Linux/AArch64" packages.

Planned DynamoRIO ARM client: `dynamorio_client/dr_crypto_profiler.c` (already ARM-agnostic; the same source compiles on aarch64 when `-DARM_64` is set instead of `-DX86_64`).

## 8. Project Cloning on ARM

```bash
git clone <repo-url> crypto-analysis
cd crypto-analysis
python3 -m venv .venv
.venv/bin/pip install pandas matplotlib
```

## 9. Sanity Check Script

```bash
./scripts/setup_arm_env.sh
./scripts/build_arm_drivers.sh
./scripts/run_arm_perf.sh
./scripts/run_arm_dynamorio.sh
```

If all four scripts complete without errors, the ARM environment is ready for live Phase 9 profiling.

## 10. Cost / Quota Notes

- Oracle's Always Free tier provides 4 OCPUs and 24 GB RAM for ARM A1.
- If capacity is unavailable, sign up for the "Free Tier" capacity notification or use a paid account with a few dollars of credit.
- Tear down the instance when not in use to avoid quota lockouts.
