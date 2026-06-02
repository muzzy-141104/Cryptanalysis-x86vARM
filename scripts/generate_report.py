#!/usr/bin/env python3

from pathlib import Path
import sys

import pandas as pd


SUMMARY_FILE = Path("results/x86/summary.csv")
REPORT_FILE = Path("results/x86/report.md")


def metric_table(df: pd.DataFrame, columns: list[str]) -> str:
    available = [col for col in columns if col in df.columns]
    if not available:
        return "No data available.\n"

    table_df = df[["algorithm"] + available].copy()
    for col in available:
        table_df[col] = pd.to_numeric(table_df[col], errors="coerce").fillna(0).astype("int64")

    headers = table_df.columns.tolist()
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for _, row in table_df.iterrows():
        values = [str(row[col]) for col in headers]
        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines) + "\n"


def observations(df: pd.DataFrame) -> list[str]:
    notes = []

    if "instruction_count" in df.columns:
        top = df.loc[pd.to_numeric(df["instruction_count"], errors="coerce").idxmax(), "algorithm"]
        notes.append(f"- Highest total instruction count: **{top}**.")

    if "memory_reads" in df.columns and "memory_writes" in df.columns:
        reads = pd.to_numeric(df["memory_reads"], errors="coerce").fillna(0)
        writes = pd.to_numeric(df["memory_writes"], errors="coerce").fillna(0)
        ratio = (reads / writes.replace(0, pd.NA)).fillna(0)
        top_ratio_idx = ratio.idxmax()
        notes.append(
            f"- Highest read/write ratio: **{df.loc[top_ratio_idx, 'algorithm']}** ({ratio.loc[top_ratio_idx]:.2f})."
        )

    aes_cols = ["aesenc_count", "aesdec_count", "aesenclast_count", "aesdeclast_count"]
    if any(col in df.columns for col in aes_cols):
        aes_total = pd.Series(0, index=df.index, dtype="int64")
        for col in aes_cols:
            if col in df.columns:
                aes_total = aes_total + pd.to_numeric(df[col], errors="coerce").fillna(0).astype("int64")
        top_aes = df.loc[aes_total.idxmax(), "algorithm"]
        notes.append(f"- Most AES hardware-op activity observed in: **{top_aes}**.")

    sha_cols = ["sha256rnds2_count", "sha256msg1_count", "sha256msg2_count"]
    if any(col in df.columns for col in sha_cols):
        sha_total = pd.Series(0, index=df.index, dtype="int64")
        for col in sha_cols:
            if col in df.columns:
                sha_total = sha_total + pd.to_numeric(df[col], errors="coerce").fillna(0).astype("int64")
        top_sha = df.loc[sha_total.idxmax(), "algorithm"]
        notes.append(f"- Most SHA hardware-op activity observed in: **{top_sha}**.")

    if not notes:
        notes.append("- No observations available; expected metrics were not present.")

    return notes


def main() -> int:
    if not SUMMARY_FILE.exists():
        print(f"Missing input file: {SUMMARY_FILE}")
        return 1

    df = pd.read_csv(SUMMARY_FILE)
    if "algorithm" not in df.columns:
        print("summary.csv must contain an 'algorithm' column")
        return 1

    lines = [
        "# x86 Cryptographic Behavior Report",
        "",
        "## Methodology",
        "",
        "Dynamic binary instrumentation is performed with Intel Pin on x86_64.",
        "Per-run profiler output is collected as metric/value CSV files, then aggregated using pandas.",
        "Visualization is generated with matplotlib and report sections are derived from summary statistics.",
        "",
        "## Benchmark Configuration",
        "",
        "- Algorithms: AES-256-CBC, SHA256, ChaCha20",
        "- Driver interface: `<binary> <data_size_bytes> <iterations>`",
        "- Typical workload: 1,048,576 bytes x 100 iterations",
        "- Host architecture: x86_64",
        "",
        "## Instruction Analysis",
        "",
        metric_table(df, ["instruction_count"]),
        "## Memory Analysis",
        "",
        metric_table(df, ["memory_reads", "memory_writes"]),
        "## AES-NI Analysis",
        "",
        metric_table(df, ["aesenc_count", "aesdec_count", "aesenclast_count", "aesdeclast_count"]),
        "## SHA-NI Analysis",
        "",
        metric_table(df, ["sha256rnds2_count", "sha256msg1_count", "sha256msg2_count"]),
        "## Observations",
        "",
    ]

    lines.extend(observations(df))
    lines.append("")

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
