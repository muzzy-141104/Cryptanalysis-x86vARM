#!/usr/bin/env python3

"""Generate cross-architecture comparison charts.

Inputs:
  results/comparison/unified_comparison.csv

Outputs (charts/):
  instructions_compare.png
  ipc_compare.png
  cycles_compare.png
  branch_miss_ratio.png
  cache_miss_ratio.png
  aes_ni_usage.png
  sha_ni_usage.png
"""

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd


COMPARISON_FILE = Path("results/comparison/unified_comparison.csv")
CHARTS_DIR = Path("charts")


def plot_bar(df: pd.DataFrame, x_col: str, value_cols, title: str, ylabel: str, output_path: Path):
    width = 0.8 / max(1, len(value_cols))
    x_positions = range(len(df))

    plt.figure(figsize=(8, 5))
    for index, col in enumerate(value_cols):
        values = pd.to_numeric(df[col], errors="coerce").fillna(0)
        offsets = [pos + index * width - 0.4 + width / 2 for pos in x_positions]
        plt.bar(offsets, values, width=width, label=col)

    plt.xticks(list(x_positions), df[x_col].astype(str).tolist())
    plt.title(title)
    plt.xlabel("Algorithm")
    plt.ylabel(ylabel)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Wrote {output_path}")


def plot_single_bar(df: pd.DataFrame, x_col: str, y_col: str, title: str, ylabel: str, output_path: Path):
    values = pd.to_numeric(df[y_col], errors="coerce").fillna(0)
    plt.figure(figsize=(8, 5))
    plt.bar(df[x_col].astype(str), values)
    plt.title(title)
    plt.xlabel("Algorithm")
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Wrote {output_path}")


def main() -> int:
    if not COMPARISON_FILE.exists():
        print(f"Missing input file: {COMPARISON_FILE}")
        print("Run scripts/run_perf.sh and scripts/compare_unified.py first.")
        return 1

    df = pd.read_csv(COMPARISON_FILE)
    if "algorithm" not in df.columns:
        print("unified_comparison.csv must contain an 'algorithm' column")
        return 1

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    if {"pin_instructions", "dynamorio_instructions", "perf_instructions"}.issubset(df.columns):
        plot_bar(
            df,
            "algorithm",
            ["pin_instructions", "dynamorio_instructions", "perf_instructions"],
            "Instruction Counts Across Profilers",
            "Instructions",
            CHARTS_DIR / "instructions_compare.png",
        )
    else:
        print("Skipping instructions_compare.png: missing columns")

    if "perf_ipc" in df.columns:
        plot_single_bar(
            df,
            "algorithm",
            "perf_ipc",
            "Instructions Per Cycle (IPC)",
            "IPC",
            CHARTS_DIR / "ipc_compare.png",
        )

    if "perf_cpu-cycles" in df.columns:
        plot_single_bar(
            df,
            "algorithm",
            "perf_cpu-cycles",
            "CPU Cycles (perf)",
            "Cycles",
            CHARTS_DIR / "cycles_compare.png",
        )

    if "perf_branch_miss_ratio" in df.columns:
        plot_single_bar(
            df,
            "algorithm",
            "perf_branch_miss_ratio",
            "Branch Miss Ratio (perf)",
            "Miss Ratio",
            CHARTS_DIR / "branch_miss_ratio.png",
        )

    if "perf_cache_miss_ratio" in df.columns:
        plot_single_bar(
            df,
            "algorithm",
            "perf_cache_miss_ratio",
            "Cache Miss Ratio (perf)",
            "Miss Ratio",
            CHARTS_DIR / "cache_miss_ratio.png",
        )

    if "aesenc_count" in df.columns and "aesenclast_count" in df.columns:
        plot_bar(
            df,
            "algorithm",
            ["aesenc_count", "aesenclast_count"],
            "AES-NI Opcode Counts",
            "Opcode Count",
            CHARTS_DIR / "aes_ni_usage.png",
        )

    if {"sha256rnds2_count", "sha256msg1_count", "sha256msg2_count"}.issubset(df.columns):
        plot_bar(
            df,
            "algorithm",
            ["sha256rnds2_count", "sha256msg1_count", "sha256msg2_count"],
            "SHA-NI Opcode Counts",
            "Opcode Count",
            CHARTS_DIR / "sha_ni_usage.png",
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
