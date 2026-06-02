#!/usr/bin/env python3

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd


SUMMARY_FILE = Path("results/x86/summary.csv")
CHARTS_DIR = Path("charts")
METRICS = ["instruction_count", "memory_reads", "memory_writes"]


def plot_bar(df: pd.DataFrame, x_col: str, y_col: str, title: str, ylabel: str, output_path: Path) -> None:
    values = pd.to_numeric(df[y_col], errors="coerce").fillna(0)
    plt.figure(figsize=(8, 5))
    plt.bar(df[x_col], values)
    plt.title(title)
    plt.xlabel("Algorithm")
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Wrote {output_path}")


def main() -> int:
    if not SUMMARY_FILE.exists():
        print(f"Missing input file: {SUMMARY_FILE}")
        return 1

    df = pd.read_csv(SUMMARY_FILE)
    if "algorithm" not in df.columns:
        print("summary.csv must contain an 'algorithm' column")
        return 1

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    for metric in METRICS:
        if metric not in df.columns:
            print(f"Skipping missing metric column: {metric}")
            continue
        output_path = CHARTS_DIR / f"{metric}.png"
        plot_bar(
            df,
            "algorithm",
            metric,
            f"{metric.replace('_', ' ').title()} Comparison",
            metric.replace("_", " ").title(),
            output_path,
        )

    aes_cols = ["aesenc_count", "aesenclast_count"]
    if all(col in df.columns for col in aes_cols):
        aes_df = df[["algorithm"] + aes_cols].copy()
        aes_df["aes_opcode_usage"] = (
            pd.to_numeric(aes_df["aesenc_count"], errors="coerce").fillna(0)
            + pd.to_numeric(aes_df["aesenclast_count"], errors="coerce").fillna(0)
        )
        plot_bar(
            aes_df,
            "algorithm",
            "aes_opcode_usage",
            "AES Opcode Usage (AESENC + AESENCLAST)",
            "Opcode Count",
            CHARTS_DIR / "aes_opcode_usage.png",
        )
    else:
        print("Skipping AES opcode chart: missing aesenc_count and/or aesenclast_count")

    sha_cols = ["sha256rnds2_count", "sha256msg1_count", "sha256msg2_count"]
    if all(col in df.columns for col in sha_cols):
        sha_df = df[["algorithm"] + sha_cols].copy()
        sha_df["sha_opcode_usage"] = (
            pd.to_numeric(sha_df["sha256rnds2_count"], errors="coerce").fillna(0)
            + pd.to_numeric(sha_df["sha256msg1_count"], errors="coerce").fillna(0)
            + pd.to_numeric(sha_df["sha256msg2_count"], errors="coerce").fillna(0)
        )
        plot_bar(
            sha_df,
            "algorithm",
            "sha_opcode_usage",
            "SHA Opcode Usage (RNDS2 + MSG1 + MSG2)",
            "Opcode Count",
            CHARTS_DIR / "sha_opcode_usage.png",
        )
    else:
        print("Skipping SHA opcode chart: missing SHA opcode columns")

    return 0


if __name__ == "__main__":
    sys.exit(main())
