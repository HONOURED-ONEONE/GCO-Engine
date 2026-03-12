# GCO Twin & Pilot Service

Provides Digital Twin simulation and Pilot orchestration for shadow-mode validation.

## Features
- **Twin Simulation**: Deterministic simulation of industrial processes based on scenarios.
- **Counterfactual Evaluation**: Evaluate the impact of corridor/weight changes before deployment.
- **Pilot Orchestration**: Run long-term shadow simulations driving the optimizer and logging synthetic KPIs.

## Safety Guarantees
- **Simulation Only**: This service does not write to real OT systems.
- **Read-Only Context**: It reads corridors and policies but never modifies them.
- **Shadow Mode**: Pilot runs are strictly virtual.

## API Endpoints

### Twin
- `POST /twin/run`: Run a simulation for a fixed horizon.
- `POST /twin/counterfactual`: Compare baseline vs adjusted scenario.
- `GET /twin/scenarios`: List available simulation scenarios.

### Pilot
- `POST /pilot/start`: Start a background shadow-mode pilot.
- `GET /pilot/health`: Check status and uptime of a pilot.
- `GET /pilot/snapshot`: Retrieve timeseries and summary of a pilot.
- `POST /pilot/stop`: Terminate a pilot.

## Scenarios
Scenarios are defined in YAML files and located in `/app/twin/scenarios`. They define:
- `initial_state`: Starting conditions.
- `parameters`: Physical constants (inertia, yield formulas).
- `disturbance_model`: Noise and drift characteristics.
