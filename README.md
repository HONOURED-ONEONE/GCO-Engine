# Golden Corridor Optimization (GCO) Engine - Phase 0

Minimal Working Skeleton for the GCO Engine MVP. This version uses Python, FastAPI, and Streamlit with local JSON persistence.

## Features
- **Six Core Endpoints:** Mode setting, Optimization recommendations, KPI ingestion, Corridor proposals, Approvals, and Versioning.
- **Pseudo-Optimizer:** Nudges process variables (temperature, flow) based on chosen optimization mode.
- **Mock MARL:** Automatically triggers corridor bound updates based on recent batch performance.
- **Local Persistence:** All state stored in `data/*.json`.
- **Synthetic Data:** Generator for time-series batch data.

## Quickstart

### 1. Installation
```bash
make install
```

### 2. Generate Synthetic Data
```bash
make data
```

### 3. Run the API
In one terminal:
```bash
make api
```

### 4. Run the UI
In another terminal:
```bash
make ui
```

## Project Structure
- `app/api/`: FastAPI backend (routers, models, services).
- `app/frontend/`: Streamlit UI.
- `data/`: JSON persistence and batch CSVs.
- `scripts/`: Data generation scripts.

## Usage Flow
1. **Select Mode:** Choose "Sustainability-first" or "Production-first" in the sidebar.
2. **Explore Batch:** Use the slider to view different points in time and see recommendations.
3. **Ingest KPIs:** Submit end-of-batch results. After 3 submissions, a proposal might be triggered.
4. **Approve Proposals:** Review and approve corridor changes in the Governance section.
