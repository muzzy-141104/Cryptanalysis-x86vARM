#!/usr/bin/env python3

from pathlib import Path
import sys

import pandas as pd


RESULTS_DIR = Path("results/x86")
OUTPUT_FILE = RESULTS_DIR / "summary.csv"

INPUT_FILES = {
    "AES": RESULTS_DIR / "aes_profile.csv",
    "SHA256": RESULTS_DIR / "sha256_profile.csv",
    "ChaCha20": RESULTS_DIR / "chacha20_profile.csv",
}

SUMMARY_COLUMNS = [
    "algorithm",
    "instruction_count",
    "memory_reads",
    "memory_writes",
    "aesenc_count",
    "aesenclast_count",
    "sha256rnds2_count",
    "sha256msg1_count",
    "sha256msg2_count",
]


def load_profile(path: Path) -> pd.Series:
    df = pd.read_csv(path)

    required_columns = {"metric", "value"}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"{path} must contain columns: metric,value")

    metric_series = df.set_index("metric")["value"]
    metric_series = pd.to_numeric(metric_series, errors="coerce")
    return metric_series


def main() -> int:
    missing = [str(path) for path in INPUT_FILES.values() if not path.exists()]
    if missing:
        print("Missing required profile files:")
        for item in missing:
            print(f"- {item}")
        return 1

    rows = []

    for algorithm, path in INPUT_FILES.items():
        metrics = load_profile(path)
        row = {"algorithm": algorithm}
        row.update(metrics.to_dict())
        rows.append(row)

    df = pd.DataFrame(rows)
    df = df.reindex(columns=SUMMARY_COLUMNS)
    df = df.fillna(0)

    for col in SUMMARY_COLUMNS[1:]:
        df[col] = df[col].astype("int64")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"Wrote {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
