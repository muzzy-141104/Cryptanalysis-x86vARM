#!/usr/bin/env python3

"""Parse per-algorithm perf CSVs into a unified machine-readable table.

Input:
  results/perf/<slug>_perf.csv  (algorithm,event,value rows)
    produced by `scripts/parse_perf_log.py`

Output:
  results/perf/perf_summary.csv
    columns: algorithm + perf events + derived metrics
"""

from pathlib import Path
import csv
import sys


PERF_DIR = Path("results/perf")
OUTPUT_FILE = PERF_DIR / "perf_summary.csv"

ALGORITHMS = [
    ("AES", "aes"),
    ("SHA256", "sha256"),
    ("ChaCha20", "chacha20"),
]

EVENTS = [
    "cpu-cycles",
    "instructions",
    "branch-instructions",
    "branch-misses",
    "cache-references",
    "cache-misses",
    "stalled-cycles-frontend",
    "stalled-cycles-backend",
]


def parse_perf_csv(path: Path) -> dict:
    metrics: dict = {event: 0 for event in EVENTS}

    if not path.exists():
        return metrics

    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            event = row.get("event")
            if event not in metrics:
                continue
            raw_value = row.get("value", "0")
            try:
                metrics[event] = int(float(raw_value))
            except (TypeError, ValueError):
                continue

    return metrics


def compute_ipc(metrics: dict) -> float:
    cycles = metrics.get("cpu-cycles") or 0
    instrs = metrics.get("instructions") or 0
    if cycles <= 0 or instrs <= 0:
        return 0.0
    return instrs / cycles


def main() -> int:
    PERF_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    header = (
        ["algorithm"]
        + EVENTS
        + ["ipc", "branch_miss_ratio", "cache_miss_ratio"]
    )

    failures = []

    for algorithm_name, slug in ALGORITHMS:
        perf_csv = PERF_DIR / f"{slug}_perf.csv"
        metrics = parse_perf_csv(perf_csv)

        cycles = metrics.get("cpu-cycles") or 0
        instrs = metrics.get("instructions") or 0
        branches = metrics.get("branch-instructions") or 0
        bmisses = metrics.get("branch-misses") or 0
        refs = metrics.get("cache-references") or 0
        cmiss = metrics.get("cache-misses") or 0

        if instrs <= 0:
            failures.append(f"{algorithm_name}: instructions counter is zero in {perf_csv}")
        if cycles <= 0:
            failures.append(f"{algorithm_name}: cpu-cycles counter is zero in {perf_csv}")

        row = [algorithm_name]
        for event in EVENTS:
            row.append(metrics.get(event) or 0)
        row.append(round(compute_ipc(metrics), 4))
        row.append(round((bmisses / branches) if branches else 0.0, 6))
        row.append(round((cmiss / refs) if refs else 0.0, 6))
        rows.append(row)

    if failures:
        print("Error: perf summary contains zero-valued counters:")
        for failure in failures:
            print(f"- {failure}")
        print("Refusing to write perf_summary.csv. Re-run perf to fix.")
        return 1

    with OUTPUT_FILE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)

    print(f"Wrote {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
