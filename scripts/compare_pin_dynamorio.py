#!/usr/bin/env python3

from pathlib import Path
import sys

import pandas as pd


PIN_RESULTS_DIR = Path("results/x86")
DR_RESULTS_DIR = Path("results/x86")
COMPARISON_DIR = Path("results/comparison")
OUTPUT_FILE = COMPARISON_DIR / "pin_vs_dynamorio.csv"

PIN_FILES = {
    "AES": "aes_profile.csv",
    "SHA256": "sha256_profile.csv",
    "ChaCha20": "chacha20_profile.csv",
}

DR_FILES = {
    "AES": "dr_aes_profile.csv",
    "SHA256": "dr_sha256_profile.csv",
    "ChaCha20": "dr_chacha20_profile.csv",
}

METRIC_MAP = {
    "instruction_count": "instr",
    "memory_reads": "reads",
    "memory_writes": "writes",
}


def load_metric(path: Path, metric: str) -> int:
    df = pd.read_csv(path)
    row = df.loc[df["metric"] == metric, "value"]
    if row.empty:
        return 0
    return int(pd.to_numeric(row.iloc[0], errors="coerce") or 0)


def main() -> int:
    rows = []
    for algorithm in PIN_FILES:
        pin_path = PIN_RESULTS_DIR / PIN_FILES[algorithm]
        dr_path = DR_RESULTS_DIR / DR_FILES[algorithm]

        if not pin_path.exists():
            print(f"Missing Pin results: {pin_path}")
            return 1
        if not dr_path.exists():
            print(f"Missing DynamoRIO results: {dr_path}")
            return 1

        row = {"algorithm": algorithm}
        for metric, suffix in METRIC_MAP.items():
            row[f"pin_{suffix}"] = load_metric(pin_path, metric)
            row[f"dynamorio_{suffix}"] = load_metric(dr_path, metric)
        rows.append(row)

    df = pd.DataFrame(rows)
    ordered = [
        "algorithm",
        "pin_instr", "dynamorio_instr",
        "pin_reads", "dynamorio_reads",
        "pin_writes", "dynamorio_writes",
    ]
    df = df[ordered]

    COMPARISON_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Wrote {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
