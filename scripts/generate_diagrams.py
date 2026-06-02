#!/usr/bin/env python3

"""Generate professional architecture diagrams for the project.

Produces SVG (vector) and PNG (raster) diagrams in docs/diagrams/:
- system_architecture
- intel_pin_pipeline
- dynamorio_pipeline
- perf_pipeline
- unified_analysis_pipeline
"""

from pathlib import Path
import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT_DIR = Path("docs/diagrams")
OUT_DIR.mkdir(parents=True, exist_ok=True)


PALETTE = {
    "app":   "#1F4E79",
    "dbi":   "#2E7D32",
    "hw":    "#B45F06",
    "data":  "#6A1B9A",
    "ana":   "#00838F",
    "arrow": "#37474F",
    "edge":  "#212121",
    "soft":  "#ECEFF1",
}


def draw_box(ax, x, y, w, h, text, fill, fontcolor="white", fontsize=10, weight="bold"):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.04,rounding_size=0.12",
        linewidth=1.2,
        edgecolor=PALETTE["edge"],
        facecolor=fill,
    )
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text,
            ha="center", va="center",
            color=fontcolor, fontsize=fontsize, fontweight=weight, wrap=True)


def draw_arrow(ax, x1, y1, x2, y2, label=None):
    arrow = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>",
        mutation_scale=18,
        color=PALETTE["arrow"],
        linewidth=1.4,
    )
    ax.add_patch(arrow)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.18, label, ha="center", va="bottom",
                fontsize=8, color=PALETTE["edge"])


def setup_axes(ax, title, xmax=12, ymax=8):
    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)


def save(fig, basename):
    svg_path = OUT_DIR / f"{basename}.svg"
    png_path = OUT_DIR / f"{basename}.png"
    fig.savefig(svg_path, format="svg", bbox_inches="tight", facecolor="white")
    fig.savefig(png_path, format="png", dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Wrote {svg_path}")
    print(f"Wrote {png_path}")


# ---------------------------------------------------------------
# 1) System Architecture
# ---------------------------------------------------------------
def diagram_system_architecture():
    fig, ax = plt.subplots(figsize=(13, 8))
    setup_axes(ax, "System Architecture: Cross-Platform Cryptographic Behavior Analysis")

    # Layer 1: Applications
    draw_box(ax, 0.5, 6.5, 2.2, 1.0, "AES-256-CBC\nDriver", PALETTE["app"])
    draw_box(ax, 3.0, 6.5, 2.2, 1.0, "SHA256\nDriver", PALETTE["app"])
    draw_box(ax, 5.5, 6.5, 2.2, 1.0, "ChaCha20\nDriver", PALETTE["app"])

    # Layer 2: DBI Engines
    draw_box(ax, 8.0, 6.5, 3.5, 1.0, "Intel Pin 4.2 (JIT)", PALETTE["dbi"])
    draw_box(ax, 8.0, 5.0, 3.5, 1.0, "DynamoRIO", PALETTE["dbi"])
    draw_box(ax, 8.0, 3.5, 3.5, 1.0, "Linux perf", PALETTE["hw"])

    # Layer 3: Profilers
    draw_box(ax, 0.5, 4.5, 3.5, 1.0, "Pin Tool:\ncrypto_profiler.cpp", PALETTE["dbi"])
    draw_box(ax, 4.5, 4.5, 3.0, 1.0, "DynamoRIO Client:\ndr_crypto_profiler.c", PALETTE["dbi"])
    draw_box(ax, 0.5, 3.0, 3.5, 1.0, "AES-NI Counter\nSHA-NI Counter", PALETTE["data"])
    draw_box(ax, 4.5, 3.0, 3.0, 1.0, "BB Aggregation\nMemory Classifier", PALETTE["data"])

    # Layer 4: Hardware
    draw_box(ax, 0.5, 1.0, 11.0, 1.2,
             "AMD Ryzen 5 7535HS | AES-NI | SHA-NI | AVX2 | PMU (perf)",
             PALETTE["hw"], fontsize=12)

    # Layer 5: Analysis
    draw_box(ax, 8.0, 1.0, 3.5, 1.2,
             "Analysis Layer\n(Python + pandas + matplotlib)",
             PALETTE["ana"], fontsize=11)

    # Arrows
    draw_arrow(ax, 1.6, 6.5, 1.6, 5.5)
    draw_arrow(ax, 4.1, 6.5, 4.1, 5.5)
    draw_arrow(ax, 6.6, 6.5, 6.6, 5.5)
    draw_arrow(ax, 4.0, 4.5, 8.0, 6.5)
    draw_arrow(ax, 6.0, 4.5, 9.75, 5.0)
    draw_arrow(ax, 9.75, 3.5, 9.75, 1.6)
    draw_arrow(ax, 6.0, 1.6, 8.0, 1.6)

    # Section labels
    ax.text(0.2, 7.2, "Workload Drivers", fontsize=10, color="#37474F")
    ax.text(8.0, 7.2, "Instrumentation Engines", fontsize=10, color="#37474F")
    ax.text(0.2, 5.2, "Profiling Implementations", fontsize=10, color="#37474F")
    ax.text(0.2, 3.7, "Metric Collection", fontsize=10, color="#37474F")
    ax.text(0.2, 1.6, "Hardware Platform", fontsize=10, color="#37474F")
    ax.text(8.0, 1.6, "Post-Processing", fontsize=10, color="#37474F")

    save(fig, "system_architecture")


# ---------------------------------------------------------------
# 2) Intel Pin pipeline
# ---------------------------------------------------------------
def diagram_pin_pipeline():
    fig, ax = plt.subplots(figsize=(13, 6))
    setup_axes(ax, "Intel Pin Profiling Pipeline")

    stages = [
        (0.3, "App Binary\naes/sha/chacha"),
        (2.3, "Pin Loader\n(pin -t tool.so)"),
        (4.3, "JIT Compiler\n+ Probe Injection"),
        (6.3, "Instruction Callbacks\nINS_InsertCall"),
        (8.3, "Counters\nInstruction / Mem / Opcode"),
        (10.3, "CSV Export\nmetric,value"),
    ]
    fills = [PALETTE["app"], PALETTE["dbi"], PALETTE["dbi"], PALETTE["dbi"], PALETTE["data"], PALETTE["ana"]]
    for (x, label), fill in zip(stages, fills):
        draw_box(ax, x, 3.5, 1.6, 1.4, label, fill, fontsize=9)

    for i in range(len(stages) - 1):
        x1 = stages[i][0] + 1.6
        x2 = stages[i + 1][0]
        draw_arrow(ax, x1, 4.2, x2, 4.2)

    # Opcode detection branch
    draw_box(ax, 6.3, 1.5, 1.6, 1.0, "XED IClass\nMatch", PALETTE["hw"], fontsize=9)
    draw_arrow(ax, 7.1, 3.5, 7.1, 2.5, label="opcode inspect")
    draw_box(ax, 8.3, 1.5, 1.6, 1.0, "AESENC / AESENCLAST\nSHA256RNDS2 / MSG1 / MSG2", PALETTE["hw"], fontsize=8)
    draw_arrow(ax, 7.9, 2.0, 8.3, 2.0, label="count++")

    # Output box
    draw_box(ax, 10.3, 1.5, 1.6, 1.0, "results/x86/*_profile.csv", PALETTE["ana"], fontsize=8)

    save(fig, "intel_pin_pipeline")


# ---------------------------------------------------------------
# 3) DynamoRIO pipeline
# ---------------------------------------------------------------
def diagram_dynamorio_pipeline():
    fig, ax = plt.subplots(figsize=(13, 6))
    setup_axes(ax, "DynamoRIO Profiling Pipeline")

    stages = [
        (0.3, "App Binary\naes/sha/chacha"),
        (2.3, "drrun -c\nlibdr_crypto_profiler.so"),
        (4.3, "BB Instrumentation\n(drmgr_register_bb)"),
        (6.3, "Per-BB Aggregation\ninstr/reads/writes"),
        (8.3, "Clean Call\n(once per BB)"),
        (10.3, "CSV Export\nmetric,value"),
    ]
    fills = [PALETTE["app"], PALETTE["dbi"], PALETTE["dbi"], PALETTE["data"], PALETTE["dbi"], PALETTE["ana"]]
    for (x, label), fill in zip(stages, fills):
        draw_box(ax, x, 3.5, 1.6, 1.4, label, fill, fontsize=9)

    for i in range(len(stages) - 1):
        x1 = stages[i][0] + 1.6
        x2 = stages[i + 1][0]
        draw_arrow(ax, x1, 4.2, x2, 4.2)

    # Memory detection helpers
    draw_box(ax, 4.3, 1.5, 1.6, 1.0, "instr_reads_memory", PALETTE["hw"], fontsize=9)
    draw_box(ax, 6.3, 1.5, 1.6, 1.0, "instr_writes_memory", PALETTE["hw"], fontsize=9)
    draw_arrow(ax, 5.1, 3.5, 5.1, 2.5, label="reads?")
    draw_arrow(ax, 7.1, 3.5, 7.1, 2.5, label="writes?")

    # Output
    draw_box(ax, 10.3, 1.5, 1.6, 1.0, "results/x86/dr_*_profile.csv", PALETTE["ana"], fontsize=8)

    save(fig, "dynamorio_pipeline")


# ---------------------------------------------------------------
# 4) perf pipeline
# ---------------------------------------------------------------
def diagram_perf_pipeline():
    fig, ax = plt.subplots(figsize=(13, 6))
    setup_axes(ax, "Linux perf Hardware Counter Pipeline")

    stages = [
        (0.3, "App Binary\naes/sha/chacha"),
        (2.3, "perf stat -e\nevents..."),
        (4.3, "Linux PMU\nCPU performance counters"),
        (6.3, "Raw perf Log\nlogs/perf/*_perf_raw.txt"),
        (8.3, "Parser\nparse_perf_log.py"),
        (10.3, "perf_summary.csv\n+ unified_comparison"),
    ]
    fills = [PALETTE["app"], PALETTE["hw"], PALETTE["hw"], PALETTE["data"], PALETTE["dbi"], PALETTE["ana"]]
    for (x, label), fill in zip(stages, fills):
        draw_box(ax, x, 3.5, 1.6, 1.4, label, fill, fontsize=9)

    for i in range(len(stages) - 1):
        x1 = stages[i][0] + 1.6
        x2 = stages[i + 1][0]
        draw_arrow(ax, x1, 4.2, x2, 4.2)

    # Event list branch
    draw_box(ax, 2.3, 1.5, 1.6, 1.4,
             "events:\ncycles\ninstructions\nbranches\nbranch-misses\ncache-refs\ncache-misses",
             PALETTE["data"], fontsize=7)
    draw_arrow(ax, 3.1, 3.5, 3.1, 2.9)

    # Derived metrics
    draw_box(ax, 8.3, 1.5, 1.6, 1.0, "IPC, branch-miss %,\ncache-miss %", PALETTE["hw"], fontsize=8)
    draw_arrow(ax, 9.1, 3.5, 9.1, 2.5)

    save(fig, "perf_pipeline")


# ---------------------------------------------------------------
# 5) Unified analysis pipeline
# ---------------------------------------------------------------
def diagram_unified_analysis():
    fig, ax = plt.subplots(figsize=(13, 8))
    setup_axes(ax, "Unified Cross-Tool Analysis Pipeline")

    # Source CSVs
    draw_box(ax, 0.3, 6.5, 2.0, 1.0, "Pin CSVs", PALETTE["dbi"])
    draw_box(ax, 0.3, 5.2, 2.0, 1.0, "DynamoRIO CSVs", PALETTE["dbi"])
    draw_box(ax, 0.3, 3.9, 2.0, 1.0, "perf CSVs", PALETTE["hw"])
    draw_box(ax, 0.3, 2.6, 2.0, 1.0, "Opcode Counts\n(AES-NI / SHA-NI)", PALETTE["data"])

    # Aggregators
    draw_box(ax, 3.5, 6.5, 2.5, 1.0, "aggregate_results.py", PALETTE["ana"])
    draw_box(ax, 3.5, 5.2, 2.5, 1.0, "compare_pin_dynamorio.py", PALETTE["ana"])
    draw_box(ax, 3.5, 3.9, 2.5, 1.0, "parse_perf_csv.py", PALETTE["ana"])
    draw_box(ax, 3.5, 2.6, 2.5, 1.0, "(inline merge)", PALETTE["ana"])

    # Unified outputs
    draw_box(ax, 7.0, 5.5, 2.5, 1.0, "summary.csv", PALETTE["data"])
    draw_box(ax, 7.0, 4.2, 2.5, 1.0, "pin_vs_dynamorio.csv", PALETTE["data"])
    draw_box(ax, 7.0, 2.9, 2.5, 1.0, "perf_summary.csv", PALETTE["data"])
    draw_box(ax, 7.0, 1.6, 2.5, 1.0, "unified_comparison.csv", PALETTE["data"])

    # Charts and report
    draw_box(ax, 10.0, 5.0, 2.0, 1.4, "generate_charts.py\ngenerate_perf_charts.py\n(PNG + SVG)", PALETTE["ana"])
    draw_box(ax, 10.0, 3.2, 2.0, 1.4, "generate_report.py\n(docs/final_report.md)", PALETTE["ana"])

    # Arrows
    for y in (6.5, 5.2, 3.9, 2.6):
        draw_arrow(ax, 2.3, y, 3.5, y)
    draw_arrow(ax, 6.0, 6.5, 7.0, 5.8)
    draw_arrow(ax, 6.0, 5.2, 7.0, 4.6)
    draw_arrow(ax, 6.0, 3.9, 7.0, 3.3)
    draw_arrow(ax, 6.0, 2.6, 7.0, 2.1)
    draw_arrow(ax, 9.5, 5.5, 10.0, 5.7)
    draw_arrow(ax, 9.5, 4.2, 10.0, 5.0)
    draw_arrow(ax, 9.5, 2.9, 10.0, 3.9)
    draw_arrow(ax, 9.5, 1.6, 10.0, 3.5)

    # Inputs/outputs labels
    ax.text(0.3, 7.2, "Per-tool CSV inputs", fontsize=10, color="#37474F")
    ax.text(3.5, 7.2, "Aggregation scripts", fontsize=10, color="#37474F")
    ax.text(7.0, 7.2, "Machine-readable tables", fontsize=10, color="#37474F")
    ax.text(10.0, 6.6, "Visualization & report", fontsize=10, color="#37474F")

    save(fig, "unified_analysis_pipeline")


# ---------------------------------------------------------------
# 6) Cross-architecture: x86 laptop + AWS Graviton ARM
# ---------------------------------------------------------------
def diagram_cross_architecture():
    fig, ax = plt.subplots(figsize=(13, 9))
    setup_axes(ax, "Cross-Architecture Pipeline: x86 Laptop + AWS Graviton ARM", xmax=13, ymax=10)

    # Source: laptop
    draw_box(ax, 0.5, 7.5, 4.0, 1.5,
             "x86 Laptop\n(AMD Ryzen 5 7535HS)\nIntel Pin + DynamoRIO + perf",
             PALETTE["app"], fontsize=11)
    ax.text(2.5, 7.0, "Builds drivers + native profiling", ha="center", va="top", fontsize=9, color="#37474F")

    # rsync
    draw_box(ax, 0.5, 5.0, 4.0, 0.8, "rsync over SSH", PALETTE["data"], fontsize=10)
    draw_arrow(ax, 2.5, 7.5, 2.5, 5.8, label="rsync")

    # Target: AWS Graviton
    draw_box(ax, 0.5, 2.5, 4.0, 1.5,
             "AWS Graviton (t4g.medium)\nUbuntu 24.04 aarch64\nDynamoRIO aarch64 + perf",
             PALETTE["dbi"], fontsize=11)
    draw_arrow(ax, 2.5, 5.0, 2.5, 4.0)

    # ARM profiling
    draw_box(ax, 0.5, 0.5, 4.0, 1.4,
             "scripts/setup_arm_env.sh\nscripts/build_arm_drivers.sh\nscripts/run_arm_perf.sh\nscripts/run_arm_dynamorio.sh",
             PALETTE["hw"], fontsize=9)

    # Pipeline stacks: perf / DynamoRIO / analysis
    draw_box(ax, 6.0, 7.5, 3.0, 1.5,
             "x86 Pipeline\nIntel Pin + AES-NI + SHA-NI\nresults/x86/*",
             PALETTE["app"], fontsize=10)
    draw_box(ax, 6.0, 5.0, 3.0, 1.5,
             "ARM Pipeline\nDynamoRIO + AESE + SHA256H\nresults/arm/*",
             PALETTE["dbi"], fontsize=10)
    draw_box(ax, 6.0, 2.5, 3.0, 1.5,
             "Cross-Arch Pipeline\nunified_comparison.csv\nx86 vs ARM tables",
             PALETTE["ana"], fontsize=10)

    # x86 perf/DynamoRIO/analysis
    draw_box(ax, 10.0, 7.5, 2.6, 1.0, "perf summary (x86)", PALETTE["hw"], fontsize=9)
    draw_box(ax, 10.0, 6.3, 2.6, 1.0, "Pin/DynamoRIO CSVs", PALETTE["dbi"], fontsize=9)
    draw_box(ax, 10.0, 5.1, 2.6, 1.0, "instruction counts", PALETTE["data"], fontsize=9)

    # ARM perf/DynamoRIO/analysis
    draw_box(ax, 10.0, 3.7, 2.6, 1.0, "perf summary (arm)", PALETTE["hw"], fontsize=9)
    draw_box(ax, 10.0, 2.5, 2.6, 1.0, "DynamoRIO CSVs (arm)", PALETTE["dbi"], fontsize=9)
    draw_box(ax, 10.0, 1.3, 2.6, 1.0, "AES-NI vs AESE counts", PALETTE["data"], fontsize=9)

    # Arrows: x86 pipeline
    draw_arrow(ax, 4.5, 8.2, 6.0, 8.2)
    draw_arrow(ax, 9.0, 8.0, 10.0, 8.0)
    draw_arrow(ax, 9.0, 7.8, 10.0, 6.8)
    draw_arrow(ax, 9.0, 7.6, 10.0, 5.6)

    # Arrows: ARM pipeline
    draw_arrow(ax, 4.5, 3.2, 6.0, 5.7)
    draw_arrow(ax, 9.0, 5.0, 10.0, 4.2)
    draw_arrow(ax, 9.0, 4.8, 10.0, 3.0)
    draw_arrow(ax, 9.0, 4.6, 10.0, 1.8)

    # Cross-arch
    draw_arrow(ax, 7.5, 7.5, 7.5, 4.0, label="merge into\nunified_comparison.csv")
    draw_arrow(ax, 11.3, 7.5, 11.3, 3.7, label="x86")
    draw_arrow(ax, 11.3, 5.0, 11.3, 3.7, label="arm")

    # Section labels
    ax.text(0.5, 9.2, "Source build host", fontsize=10, color="#37474F")
    ax.text(0.5, 6.0, "Transfer (rsync over SSH)", fontsize=10, color="#37474F")
    ax.text(0.5, 4.1, "Profiling target", fontsize=10, color="#37474F")
    ax.text(0.5, 2.0, "Automation scripts", fontsize=10, color="#37474F")
    ax.text(6.0, 9.2, "Pipelines", fontsize=10, color="#37474F")
    ax.text(10.0, 8.7, "x86 outputs", fontsize=10, color="#37474F")
    ax.text(10.0, 4.7, "ARM outputs", fontsize=10, color="#37474F")

    save(fig, "cross_architecture_pipeline")


def main():
    diagram_system_architecture()
    diagram_pin_pipeline()
    diagram_dynamorio_pipeline()
    diagram_perf_pipeline()
    diagram_unified_analysis()
    diagram_cross_architecture()


if __name__ == "__main__":
    main()
