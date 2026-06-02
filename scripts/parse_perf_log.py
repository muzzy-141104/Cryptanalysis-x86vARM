#!/usr/bin/env python3

"""Parse the human-readable perf stat log into a per-algorithm CSV.

Input:
  arguments: <perf_dir> <algorithm_slug> <perf_log> <output_csv>

Output CSV columns (one row per event):
  algorithm,event,value

The upstream parser `parse_perf_csv.py` consumes the per-algorithm
CSVs and produces `perf_summary.csv`.
"""

from pathlib import Path
import csv
import re
import sys


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

# perf stat on Ubuntu 24.04 prints short aliases for some events.
EVENT_ALIASES = {
    "cpu-cycles": ["cpu-cycles", "cycles"],
    "instructions": ["instructions"],
    "branch-instructions": ["branch-instructions", "branches"],
    "branch-misses": ["branch-misses"],
    "cache-references": ["cache-references"],
    "cache-misses": ["cache-misses"],
    "stalled-cycles-frontend": ["stalled-cycles-frontend"],
    "stalled-cycles-backend": ["stalled-cycles-backend"],
}

# Build reverse map from alias to canonical name
ALIAS_TO_CANONICAL: dict = {}
for canonical, aliases in EVENT_ALIASES.items():
    for alias in aliases:
        ALIAS_TO_CANONICAL[alias] = canonical

NUMBER_RE = re.compile(r"([0-9][0-9,\.]*)")

# Lines we always skip, regardless of event matching
SKIP_PATTERNS = (
    "seconds time elapsed",
    "seconds user",
    "seconds sys",
    "Performance counter stats",
)


def extract_event_name(stripped: str) -> str:
    """Return the canonical event name for a perf stat data line.

    perf stat layout: <number> <event_name> [annotation...]
    We split on the first whitespace-run after the number, and look up
    the second token in the alias map.
    """
    parts = stripped.split()
    if len(parts) < 2:
        return ""

    # parts[0] is the counter value, parts[1] is the event name as printed.
    candidate = parts[1]

    if candidate in ALIAS_TO_CANONICAL:
        return ALIAS_TO_CANONICAL[candidate]

    return ""


def parse_value(stripped: str) -> int:
    parts = stripped.split()
    if not parts:
        return 0
    raw = parts[0]
    cleaned = raw.replace(",", "")
    try:
        return int(cleaned)
    except ValueError:
        try:
            return int(float(cleaned))
        except ValueError:
            return 0


def parse_line(line: str) -> tuple:
    """Return (canonical_event, value) for a perf stat data line or (None, None)."""
    stripped = line.strip()
    if not stripped:
        return None, None

    if stripped.startswith("#"):
        return None, None

    if any(pattern in stripped for pattern in SKIP_PATTERNS):
        return None, None

    if stripped.lower().startswith("<not supported"):
        for alias in stripped.split()[1:]:
            canonical = ALIAS_TO_CANONICAL.get(alias)
            if canonical is not None:
                return canonical, 0
        return None, None

    canonical = extract_event_name(stripped)
    if not canonical:
        return None, None

    return canonical, parse_value(stripped)


def main() -> int:
    if len(sys.argv) != 5:
        print("Usage: parse_perf_log.py <perf_dir> <slug> <log> <out_csv>")
        return 1

    perf_dir = Path(sys.argv[1])
    slug = sys.argv[2]
    log_path = Path(sys.argv[3])
    output_csv = Path(sys.argv[4])

    perf_dir.mkdir(parents=True, exist_ok=True)

    metrics: dict = {}

    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            event, value = parse_line(line)
            if event is None:
                continue
            if event in metrics:
                continue
            metrics[event] = value

    missing = [event for event in EVENTS if event not in metrics]
    if missing:
        print(f"Warning: missing perf events in {log_path}: {missing}")

    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["algorithm", "event", "value"])
        for event in EVENTS:
            writer.writerow([slug, event, metrics.get(event, 0)])

    print(f"Wrote {output_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
