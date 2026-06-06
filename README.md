# Cryptanalysis-x86vARM

Cross-architecture cryptographic behavior analysis comparing **x86_64**
(AMD Ryzen 5 7535HS) and **ARMv8 (AWS Graviton2 / Neoverse-N1)** using
three independent measurement backends: **Intel Pin**, **DynamoRIO**, and
the Linux **`perf`** subsystem.

The project produces instruction-level, memory-traffic, branch/cache, and
crypto-extension opcode metrics for **AES-256-CBC**, **SHA-256**, and
**ChaCha20**, then compares the two architectures on a unified pipeline.

## Status

- **x86 pipeline**: stable. Pin and DynamoRIO instruction counts agree
  within 0.4%; `perf` hardware counters agree within 1-3%.
- **ARM pipeline**: implemented and validated. Native `armv8_pmuv3_0` events
  are used. On the Graviton2 instance used here, retired-instruction,
  branch, and cache PMU events are restricted by the hypervisor and are
  reported as `N/A`; cycles and wall-clock throughput are unaffected.
- **Cross-architecture comparison**: produced from available fields.
- **Dashboard**: local FastAPI + Vite/React/Tailwind UI.

## Repository layout

```
Cryptanalysis-x86vARM/
├── drivers/                 AES, SHA256, ChaCha20 OpenSSL drivers
├── pin_tool/                Intel Pin DBI profiler
├── dynamorio_client/        DynamoRIO DBI profiler
├── scripts/                 Pipeline automation (x86 + ARM + dashboard)
├── results/                 CSV outputs
│   ├── x86/                 Pin + DR per-algorithm profiles + summary
│   ├── arm/                 ARM summary, perf_summary, PMU validation
│   ├── perf/                perf hardware counter summary (x86)
│   └── comparison/          x86_vs_arm.csv, unified_comparison.csv
├── charts/                  Generated PNG charts
├── docs/                    Reports and design docs
└── dashboard/               Local FastAPI + React dashboard
    ├── backend/             FastAPI app
    ├── frontend/            Vite + React + Tailwind UI
    └── dashboard_screenshots/
```

## Quick start

### x86 analysis

```bash
./scripts/build_arm_drivers.sh    # or your x86 build equivalent
./scripts/run_perf.sh             # perf hardware counters
./scripts/run_all.sh              # full pipeline (Pin + DR + perf + charts + report)
```

### ARM analysis (Graviton)

```bash
./scripts/setup_arm_env.sh
./scripts/build_arm_drivers.sh
./scripts/run_arm_perf.sh                 # uses native armv8_pmuv3_0 events
.venv/bin/python scripts/generate_arm_phase8c.py
```

Outputs:
- `results/arm/summary.csv` — throughput, execution time, cycles, crypto extension availability
- `results/arm/perf_summary.csv` — per-event PMU values (N/A where restricted)
- `results/arm/available_pmu_events.txt` — discovered `armv8_pmuv3_0` events
- `results/arm/pmu_validation.csv` — per-event validation status
- `results/comparison/x86_vs_arm.csv` — cross-architecture comparison
- `charts/x86_vs_arm_throughput.png`, `charts/x86_vs_arm_cycles.png`

### Dashboard

```bash
# Terminal 1: backend (port 8000)
cd dashboard/backend && ./run.sh

# Terminal 2: frontend (port 5173, proxies /api -> :8000)
cd dashboard/frontend && ./run.sh
```

Or build once and serve the UI from FastAPI:

```bash
cd dashboard/frontend && BUILD=1 ./run.sh
cd ../backend && ./run.sh
# open http://localhost:8000/
```

If the data and the browser are on different hosts, use an SSH local
forward (preferred) or open inbound TCP 8000/5173 in the security group.

## Pipeline summary

```
drivers/  --[pin|DynamoRIO|perf]-->  results/{x86,arm,perf}/*.csv
                                       |
                                       v
                           scripts/compare_unified.py
                                       |
                                       v
                       results/comparison/unified_comparison.csv
                                       |
                          +------------+------------+
                          v                         v
              scripts/generate_charts.py   scripts/generate_arm_phase8c.py
                          |                         |
                          v                         v
                    charts/*.png       results/comparison/x86_vs_arm.csv
                                                       |
                                                       v
                                          dashboard/backend + frontend
```

## ARM PMU mapping (x86 alias -> armv8_pmuv3_0)

| Analysis metric | x86 alias | ARM PMUv3 event |
|---|---|---|
| Instructions | `instructions` | `inst_retired` |
| Branch instructions | `branch-instructions` | `br_retired` |
| Branch misses | `branch-misses` | `br_mis_pred_retired` |
| L1D cache accesses | `cache-references` | `l1d_cache` |
| L1D cache refills | `cache-misses` | `l1d_cache_refill` |
| L1I cache accesses | N/A | `l1i_cache` |
| L1I cache refills | N/A | `l1i_cache_refill` |
| Frontend stalls | `stalled-cycles-frontend` | `stall_frontend` |
| Backend stalls | `stalled-cycles-backend` | `stall_backend` |

The mapping is encoded in `scripts/parse_perf_log.py`. See
`docs/arm_pmu_analysis.md` for the full discussion and validation status.

## Reports

- `docs/final_report.md` — main x86 report
- `docs/final_project_report.md` — combined x86 + ARM cross-architecture report
- `docs/arm_analysis.md` — ARM Graviton analysis and PMU limitation discussion
- `docs/arm_pmu_analysis.md` — ARM PMU discovery and event mapping
- `docs/aws_graviton_setup.md` — provisioning
- `docs/x86_vs_arm_design.md` — comparison design templates
- `docs/perf_analysis.md`, `docs/results_appendix.md`, `docs/reproducibility.md`
- `dashboard/README.md` — dashboard startup

## Reproducibility

Per-architecture:

- x86: `./scripts/run_all.sh`
- ARM: `./scripts/run_arm_perf.sh` and
  `python3 scripts/generate_arm_phase8c.py`

Cross-architecture and visualization:

- `python3 scripts/compare_unified.py` (unified comparison CSV)
- `python3 scripts/generate_arm_phase8c.py` (ARM summary + x86 vs ARM CSV + charts)
- `python3 scripts/generate_perf_charts.py` (perf comparison charts)

All CSVs are committed so the dashboard can be served without re-running
the analysis.

## Limitations

1. Single host per architecture. Other CPUs may dispatch OpenSSL
   differently.
2. Single workload size (1 MB x 100 iterations).
3. On this Graviton2 environment, PMU access for non-privileged workloads
   is restricted; retired-instruction, branch, and cache counters are
   reported as `N/A`. Cycles and wall-clock throughput are unaffected.
4. x86 wall-clock throughput is not collected alongside ARM in this run;
   `x86_throughput` is `N/A` in `results/comparison/x86_vs_arm.csv`.
