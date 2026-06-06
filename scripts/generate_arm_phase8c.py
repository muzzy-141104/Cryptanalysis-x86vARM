#!/usr/bin/env python3

from pathlib import Path
import csv
import re

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ARM_LOG_DIR = ROOT / "logs/perf_arm"
ARM_SUMMARY_FILE = ROOT / "results/arm/summary.csv"
X86_PERF_FILE = ROOT / "results/perf/perf_summary.csv"
ARM_PERF_FILE = ROOT / "results/arm/perf_summary.csv"
COMPARISON_FILE = ROOT / "results/comparison/x86_vs_arm.csv"
CHARTS_DIR = ROOT / "charts"

ALGORITHMS = ["aes", "sha256", "chacha20"]
NAMES = {"aes": "AES", "sha256": "SHA256", "chacha20": "ChaCha20"}
TOTAL_MB = 100.0


def parse_arm_log(slug: str) -> tuple[float, int]:
    log_path = ARM_LOG_DIR / f"{slug}_perf.log"
    text = log_path.read_text(encoding="utf-8", errors="replace")

    elapsed_match = re.search(r"\n\s*([0-9]+\.[0-9]+)\s+seconds time elapsed", text)
    cycles_match = re.search(r"\n\s*([0-9,]+)\s+cpu_cycles", text)

    elapsed = float(elapsed_match.group(1)) if elapsed_match else 0.0
    cycles = int(cycles_match.group(1).replace(",", "")) if cycles_match else 0
    return elapsed, cycles


def load_x86_cycles() -> dict:
    df = pd.read_csv(X86_PERF_FILE)
    out = {}
    for _, row in df.iterrows():
        out[row["algorithm"]] = int(row.get("cpu-cycles", 0))
    return out


def load_arm_perf_cycles() -> dict:
    df = pd.read_csv(ARM_PERF_FILE)
    out = {}
    for _, row in df.iterrows():
        value = row.get("cpu-cycles", "0")
        try:
            out[row["algorithm"]] = int(value)
        except (TypeError, ValueError):
            out[row["algorithm"]] = 0
    return out


def write_arm_summary() -> None:
    rows = []
    for slug in ALGORITHMS:
        elapsed, cycles = parse_arm_log(slug)
        throughput = (TOTAL_MB / elapsed) if elapsed > 0 else "N/A"
        crypto = "yes" if slug in ("aes", "sha256") else "no"
        rows.append(
            {
                "algorithm": NAMES[slug],
                "throughput": round(throughput, 2) if isinstance(throughput, float) else "N/A",
                "execution_time": round(elapsed, 6) if elapsed > 0 else "N/A",
                "cycles": cycles if cycles > 0 else "N/A",
                "crypto_extensions_present": crypto,
            }
        )

    ARM_SUMMARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with ARM_SUMMARY_FILE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "algorithm",
                "throughput",
                "execution_time",
                "cycles",
                "crypto_extensions_present",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_comparison_and_charts() -> None:
    x86_cycles = load_x86_cycles()
    arm_cycles = load_arm_perf_cycles()
    arm_summary = pd.read_csv(ARM_SUMMARY_FILE)
    arm_summary = arm_summary.set_index("algorithm").to_dict(orient="index")

    rows = []
    for alg in ["AES", "SHA256", "ChaCha20"]:
        arm = arm_summary.get(alg, {})
        x86_c = x86_cycles.get(alg, 0)
        arm_c = arm_cycles.get(alg, 0)
        arm_t = arm.get("throughput", "N/A")
        arm_e = arm.get("execution_time", "N/A")
        rows.append(
            {
                "algorithm": alg,
                "x86_throughput": "N/A",
                "arm_throughput": arm_t,
                "x86_execution_time": "N/A",
                "arm_execution_time": arm_e,
                "x86_cycles": x86_c if x86_c > 0 else "N/A",
                "arm_cycles": arm_c if arm_c > 0 else "N/A",
                "x86_crypto_extensions_present": "yes",
                "arm_crypto_extensions_present": "yes" if alg in ("AES", "SHA256") else "no",
            }
        )

    COMPARISON_FILE.parent.mkdir(parents=True, exist_ok=True)
    comp_df = pd.DataFrame(rows)
    comp_df.to_csv(COMPARISON_FILE, index=False)

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    # Throughput chart (ARM bars; x86 unavailable in this environment)
    tdf = comp_df.copy()
    tdf["arm_throughput"] = pd.to_numeric(tdf["arm_throughput"], errors="coerce")
    tdf["x86_throughput"] = pd.to_numeric(tdf["x86_throughput"], errors="coerce")
    x = range(len(tdf))
    width = 0.35
    plt.figure(figsize=(8, 5))
    plt.bar([i - width / 2 for i in x], tdf["x86_throughput"].fillna(0), width=width, label="x86")
    plt.bar([i + width / 2 for i in x], tdf["arm_throughput"].fillna(0), width=width, label="ARM")
    plt.xticks(list(x), tdf["algorithm"].tolist())
    plt.title("x86 vs ARM Throughput (MB/s)")
    plt.ylabel("MB/s")
    plt.xlabel("Algorithm")
    plt.legend()
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "x86_vs_arm_throughput.png", dpi=150)
    plt.close()

    # Cycles chart
    cdf = comp_df.copy()
    cdf["x86_cycles"] = pd.to_numeric(cdf["x86_cycles"], errors="coerce")
    cdf["arm_cycles"] = pd.to_numeric(cdf["arm_cycles"], errors="coerce")
    x = range(len(cdf))
    plt.figure(figsize=(8, 5))
    plt.bar([i - width / 2 for i in x], cdf["x86_cycles"].fillna(0), width=width, label="x86")
    plt.bar([i + width / 2 for i in x], cdf["arm_cycles"].fillna(0), width=width, label="ARM")
    plt.xticks(list(x), cdf["algorithm"].tolist())
    plt.title("x86 vs ARM Cycles")
    plt.ylabel("Cycles")
    plt.xlabel("Algorithm")
    plt.legend()
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / "x86_vs_arm_cycles.png", dpi=150)
    plt.close()


def main() -> int:
    write_arm_summary()
    write_comparison_and_charts()
    print(f"Wrote {ARM_SUMMARY_FILE}")
    print(f"Wrote {COMPARISON_FILE}")
    print(f"Wrote {CHARTS_DIR / 'x86_vs_arm_throughput.png'}")
    print(f"Wrote {CHARTS_DIR / 'x86_vs_arm_cycles.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
