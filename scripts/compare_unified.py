#!/usr/bin/env python3

"""Merge perf hardware counters with Pin, DynamoRIO, and opcode-aware metrics.

Inputs:
  results/perf/perf_summary.csv
  results/x86/aes_profile.csv
  results/x86/sha256_profile.csv
  results/x86/chacha20_profile.csv
  results/x86/dr_aes_profile.csv
  results/x86/dr_sha256_profile.csv
  results/x86/dr_chacha20_profile.csv

Output:
  results/comparison/unified_comparison.csv
"""

from pathlib import Path
import csv
import sys


X86_DIR = Path("results/x86")
PERF_FILE = Path("results/perf/perf_summary.csv")
OUTPUT_FILE = Path("results/comparison/unified_comparison.csv")

ALGORITHMS = ["AES", "SHA256", "ChaCha20"]
DR_FILES = {
    "AES": "dr_aes_profile.csv",
    "SHA256": "dr_sha256_profile.csv",
    "ChaCha20": "dr_chacha20_profile.csv",
}
PIN_FILES = {
    "AES": "aes_profile.csv",
    "SHA256": "sha256_profile.csv",
    "ChaCha20": "chacha20_profile.csv",
}

PERF_COLUMNS = [
    "cpu-cycles",
    "instructions",
    "branch-instructions",
    "branch-misses",
    "cache-references",
    "cache-misses",
    "stalled-cycles-frontend",
    "stalled-cycles-backend",
    "ipc",
    "branch_miss_ratio",
    "cache_miss_ratio",
]


def load_metric(path: Path, metric: str) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("metric") == metric:
                value = row.get("value", "0")
                try:
                    return int(float(value))
                except ValueError:
                    return 0
    return 0


def load_perf(path: Path) -> dict:
    """Return {algorithm_name: {column: float, ...}, ...} from perf_summary.csv."""
    result: dict = {}
    if not path.exists():
        return result
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            name = row.get("algorithm")
            if not name:
                continue
            result[name] = {}
            for column in PERF_COLUMNS:
                value = row.get(column, "0")
                try:
                    result[name][column] = float(value)
                except ValueError:
                    result[name][column] = 0.0
    return result


def main() -> int:
    perf_data = load_perf(PERF_FILE)

    rows = []
    header = (
        ["algorithm"]
        + [f"perf_{c}" for c in PERF_COLUMNS]
        + [
            "pin_instructions",
            "dynamorio_instructions",
            "pin_memory_reads",
            "pin_memory_writes",
            "aesenc_count",
            "aesenclast_count",
            "sha256rnds2_count",
            "sha256msg1_count",
            "sha256msg2_count",
        ]
    )

    for algorithm in ALGORITHMS:
        pin_path = X86_DIR / PIN_FILES[algorithm]
        dr_path = X86_DIR / DR_FILES[algorithm]

        row = [algorithm]
        perf_alg = perf_data.get(algorithm, {})
        for column in PERF_COLUMNS:
            value = perf_alg.get(column, 0.0)
            row.append(int(value) if column not in ("ipc", "branch_miss_ratio", "cache_miss_ratio") else value)

        row.append(load_metric(pin_path, "instruction_count"))
        row.append(load_metric(dr_path, "instruction_count"))
        row.append(load_metric(pin_path, "memory_reads"))
        row.append(load_metric(pin_path, "memory_writes"))
        row.append(load_metric(pin_path, "aesenc_count"))
        row.append(load_metric(pin_path, "aesenclast_count"))
        row.append(load_metric(pin_path, "sha256rnds2_count"))
        row.append(load_metric(pin_path, "sha256msg1_count"))
        row.append(load_metric(pin_path, "sha256msg2_count"))
        rows.append(row)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)

    print(f"Wrote {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
