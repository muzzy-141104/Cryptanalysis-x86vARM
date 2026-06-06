"""FastAPI backend for the Cryptanalysis-x86vARM dashboard.

Endpoints:
  /api/x86         -> x86 DBI/perf/opcode summary (results/x86, results/perf)
  /api/arm         -> ARM perf + summary (results/arm)
  /api/comparison  -> cross-architecture comparison CSV
  /api/charts      -> chart inventory (PNG files in charts/)
  /api/reports     -> markdown reports (arm_analysis.md, final_project_report.md)
  /api/overview    -> top-level project metadata
  /api/raw/{kind}  -> raw CSV (kind in {"x86","arm","comparison"})

The backend reads CSV/Markdown/PNG files from the project root and serves
them as JSON, text, or static files. It does not generate new analysis.
"""

from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parents[2])).resolve()
RESULTS = ROOT / "results"
CHARTS = ROOT / "charts"
DOCS = ROOT / "docs"
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _coerce(value: str) -> Any:
    if value is None:
        return None
    text = value.strip()
    if text in ("", "N/A", "n/a", "NA"):
        return None
    try:
        if text.replace(".", "", 1).lstrip("-").isdigit():
            return int(text) if "." not in text else float(text)
        return float(text)
    except (TypeError, ValueError):
        return value


def _load_table(path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path)
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append({key: _coerce(value) for key, value in row.items()})
    return out


def _load_charts() -> list[dict[str, str]]:
    if not CHARTS.exists():
        return []
    items: list[dict[str, str]] = []
    for chart in sorted(CHARTS.glob("*.png")):
        items.append(
            {
                "name": chart.stem,
                "title": chart.stem.replace("_", " ").title(),
                "url": f"/static/charts/{chart.name}",
            }
        )
    return items


def _load_reports() -> list[dict[str, str]]:
    candidates = [
        ("arm_analysis.md", "ARM Analysis"),
        ("final_project_report.md", "Final Project Report"),
    ]
    out: list[dict[str, str]] = []
    for filename, title in candidates:
        path = DOCS / filename
        if not path.exists():
            continue
        out.append({"slug": path.stem, "title": title, "content": path.read_text(encoding="utf-8")})
    return out


app = FastAPI(title="Cryptanalysis-x86vARM Dashboard", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/overview")
def overview() -> dict[str, Any]:
    return {
        "project": "Cryptanalysis-x86vARM",
        "description": (
            "Cross-architecture cryptographic behavior analysis comparing x86_64 and "
            "ARMv8 (Graviton2) using Intel Pin, DynamoRIO, and Linux perf."
        ),
        "algorithms": [
            {"name": "AES-256-CBC", "description": "OpenSSL EVP_aes_256_cbc()"},
            {"name": "SHA256", "description": "OpenSSL EVP_sha256()"},
            {"name": "ChaCha20", "description": "OpenSSL EVP_chacha20()"},
        ],
        "architectures": [
            {
                "name": "x86_64",
                "host": "AMD Ryzen 5 7535HS",
                "extensions": ["AES-NI", "SHA-NI"],
                "tools": ["Intel Pin", "DynamoRIO", "Linux perf"],
            },
            {
                "name": "ARMv8 (Graviton2)",
                "host": "AWS t4g.medium (Neoverse-N1)",
                "extensions": ["AESE", "AESD", "AESMC", "AESIMC", "SHA256H", "SHA256H2", "SHA256SU0", "SHA256SU1"],
                "tools": ["DynamoRIO", "Linux perf (armv8_pmuv3_0)"],
            },
        ],
    }


@app.get("/api/x86")
def x86_data() -> dict[str, Any]:
    return {
        "summary": _load_table(RESULTS / "x86" / "summary.csv"),
        "perf_summary": _load_table(RESULTS / "perf" / "perf_summary.csv"),
        "unified_comparison": _load_table(RESULTS / "comparison" / "unified_comparison.csv"),
    }


@app.get("/api/arm")
def arm_data() -> dict[str, Any]:
    return {
        "summary": _load_table(RESULTS / "arm" / "summary.csv"),
        "perf_summary": _load_table(RESULTS / "arm" / "perf_summary.csv"),
        "pmu_validation": _load_table(RESULTS / "arm" / "pmu_validation.csv"),
        "available_events": (RESULTS / "arm" / "available_pmu_events.txt").read_text(encoding="utf-8").splitlines()
        if (RESULTS / "arm" / "available_pmu_events.txt").exists()
        else [],
    }


@app.get("/api/comparison")
def comparison_data() -> dict[str, Any]:
    return {
        "x86_vs_arm": _load_table(RESULTS / "comparison" / "x86_vs_arm.csv"),
        "unified": _load_table(RESULTS / "comparison" / "unified_comparison.csv"),
        "pin_vs_dynamorio": _load_table(RESULTS / "comparison" / "pin_vs_dynamorio.csv"),
    }


@app.get("/api/charts")
def charts() -> list[dict[str, str]]:
    return _load_charts()


@app.get("/api/reports")
def reports() -> list[dict[str, str]]:
    return _load_reports()


@app.get("/api/raw/x86")
def raw_x86() -> JSONResponse:
    return JSONResponse(_load_table(RESULTS / "x86" / "summary.csv"))


@app.get("/api/raw/arm")
def raw_arm() -> JSONResponse:
    return JSONResponse(_load_table(RESULTS / "arm" / "summary.csv"))


@app.get("/api/raw/comparison")
def raw_comparison() -> JSONResponse:
    return JSONResponse(_load_table(RESULTS / "comparison" / "x86_vs_arm.csv"))


# Static assets
if CHARTS.exists():
    app.mount("/static/charts", StaticFiles(directory=CHARTS), name="charts")


# Serve built frontend if available
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")


def _cli() -> None:
    import uvicorn

    host = os.environ.get("DASHBOARD_HOST", "0.0.0.0")
    port = int(os.environ.get("DASHBOARD_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    _cli()
