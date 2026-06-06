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


DEFAULT_PERF_DIR = Path("results/perf")

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


def fmt_counter(event: str, value: int) -> str:
    if event == "cpu-cycles":
        return str(value)
    if value <= 0:
        return "N/A"
    return str(value)


def main() -> int:
    perf_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PERF_DIR
    output_file = perf_dir / "perf_summary.csv"

    perf_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    header = (
        ["algorithm"]
        + EVENTS
        + ["ipc", "branch_miss_ratio", "cache_miss_ratio"]
    )

    for algorithm_name, slug in ALGORITHMS:
        perf_csv = perf_dir / f"{slug}_perf.csv"
        metrics = parse_perf_csv(perf_csv)

        cycles = metrics.get("cpu-cycles") or 0
        instrs = metrics.get("instructions") or 0
        branches = metrics.get("branch-instructions") or 0
        bmisses = metrics.get("branch-misses") or 0
        refs = metrics.get("cache-references") or 0
        cmiss = metrics.get("cache-misses") or 0

        row = [algorithm_name]
        for event in EVENTS:
            row.append(fmt_counter(event, metrics.get(event) or 0))

        ipc = round(compute_ipc(metrics), 4) if cycles > 0 and instrs > 0 else "N/A"
        bmr = round((bmisses / branches), 6) if branches > 0 else "N/A"
        cmr = round((cmiss / refs), 6) if refs > 0 else "N/A"

        row.append(ipc)
        row.append(bmr)
        row.append(cmr)
        rows.append(row)

    with output_file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)

    print(f"Wrote {output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
