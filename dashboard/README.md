# Cryptanalysis-x86vARM Dashboard

A local dashboard that visualizes the complete x86 and ARM analysis pipeline.

## Stack

- **Frontend**: React + Vite + TailwindCSS
- **Backend**: FastAPI (Python)

The backend reads the existing CSV files in `results/` and PNG charts in
`charts/`. It does not run the analysis — it only serves the artifacts.

## Layout

```
dashboard/
  backend/                 FastAPI app
    main.py
    requirements.txt
    run.sh
    package.json
  frontend/                Vite + React + Tailwind app
    index.html
    src/
      App.jsx
      main.jsx
      index.css
      lib/
        api.js
        useApi.js
      components/
        Card.jsx
        DataTable.jsx
        Loader.jsx
        ErrorBox.jsx
      pages/
        Overview.jsx
        X86.jsx
        Arm.jsx
        Comparison.jsx
        Charts.jsx
        Report.jsx
    vite.config.js
    tailwind.config.js
    postcss.config.js
    package.json
    run.sh
  dashboard_screenshots/   place captured screenshots here
```

## Setup

### Backend

```bash
cd dashboard/backend
./run.sh
```

This creates `.venv/`, installs `fastapi` and `uvicorn`, and starts the API
on `http://0.0.0.0:8000`. The API is configured to read from the project
root (`PROJECT_ROOT` env var, defaults to `dashboard/../..`).

### Frontend (dev)

```bash
cd dashboard/frontend
./run.sh
```

Vite starts on `http://localhost:5173` and proxies `/api` and `/static` to
the FastAPI server on port 8000.

### Frontend (build + serve from backend)

```bash
cd dashboard/frontend
BUILD=1 ./run.sh
cd ../backend
./run.sh
```

The backend will then serve the built `dist/` at `http://localhost:8000/`.

## Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/overview` | Project summary, algorithms, architectures |
| `GET /api/x86` | x86 DBI summary, perf summary, unified comparison |
| `GET /api/arm` | ARM throughput summary, perf summary, PMU validation, available events |
| `GET /api/comparison` | x86 vs ARM, unified, pin vs DynamoRIO |
| `GET /api/charts` | Chart inventory (PNG metadata) |
| `GET /api/reports` | ARM analysis + final project report (rendered as Markdown) |
| `GET /api/raw/{x86,arm,comparison}` | Raw CSV rows |
| `GET /static/charts/{file}` | Chart PNG files |

## Pages

| Path | Page |
|---|---|
| `/` | Overview |
| `/x86` | x86 Analysis |
| `/arm` | ARM Analysis |
| `/comparison` | Comparison |
| `/charts` | Charts Gallery |
| `/report` / `/report/:slug` | Report Viewer |

## Access across hosts

The backend and frontend bind to `0.0.0.0`, but EC2 security groups block
inbound traffic by default. Two options:

1. Open inbound TCP 8000 (and 5173 for dev) to your IP in the security
   group, then open `http://<instance-ip>:8000/` (or `:5173/`).
2. Use an SSH local port forward from your laptop (no security-group
   changes):

   ```bash
   ssh -i ~/Downloads/graviton-key.pem \
       -L 8000:127.0.0.1:8000 \
       -L 5173:127.0.0.1:5173 \
       ubuntu@<INSTANCE_PUBLIC_IP>
   ```

   Then run the backend (and optionally the frontend) on the instance and
   open `http://localhost:8000/` on your laptop.

## Screenshots

Drop captures of each page into `dashboard/dashboard_screenshots/`:

```
dashboard/dashboard_screenshots/
  overview.png
  x86.png
  arm.png
  comparison.png
  charts.png
  report.png
```
