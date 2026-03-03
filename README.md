# Golden Corridor Optimization Engine (Track B)

## Overview
GCO Engine is a production-like optimization platform for industrial corridors, focusing on balancing energy, quality, and yield.

## Phase 1 – Mode Configuration & Hardening (Current)
Phase 1 evolves the basic mode toggle into a robust module with validation, persistence, and audit logging.

### Key Features
- **Backend (FastAPI)**: Hardened endpoints for setting and getting optimization modes.
- **Services**: Centralized logic for mode definitions and audit logging.
- **Persistence**: Safe file-backed JSON storage with locking for concurrent writes.
- **Frontend (Streamlit)**: Enhanced UI for mode management and policy visualization.
- **Testing**: Comprehensive unit and integration tests for mode operations.

### Allowed Modes
- `sustainability_first`: Energy=0.60, Quality=0.25, Yield=0.15
- `production_first`: Energy=0.25, Quality=0.35, Yield=0.40

## Getting Started

1. **Install Dependencies**:
   ```bash
   make install
   ```

2. **Generate Synthetic Data**:
   ```bash
   make data
   ```

3. **Run the API**:
   ```bash
   make run-api
   ```

4. **Run the Frontend**:
   ```bash
   make run-frontend
   ```

5. **Run Tests**:
   ```bash
   make test
   ```

## Development Commands
- `make reset-mode`: Restore default optimization mode in the registry.
- `make demo-mode`: Start both API and Frontend for a quick demo.

## Data Structure
- `data/version_registry.json`: Tracks active mode, weights, and audit history.
- `data/corridor.json`: Stores corridor bounds and version history.
- `data/kpi_store.json`: Stores end-of-batch KPI records.
