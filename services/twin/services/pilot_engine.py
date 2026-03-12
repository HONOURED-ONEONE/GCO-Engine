import asyncio
import time
from typing import Dict, Any, List, Optional
from ..models.schemas import PilotStartRequest, PilotHealthResponse, PilotSnapshotResponse
from ..clients.optimizer_client import optimizer_client
from ..services.simulator import Simulator
from ..services.scenarios import manager

class PilotContext:
    def __init__(self, req: PilotStartRequest):
        self.pilot_id = req.pilot_id
        self.scenario_id = req.scenario_id
        self.mode = req.mode
        self.horizon_minutes = req.horizon_minutes
        self.seed = req.seed
        
        self.status = "running"
        self.start_time = time.time()
        self.step_index = 0
        self.timeseries: List[Dict[str, Any]] = []
        self.kpis: List[Dict[str, Any]] = []
        self.last_step_data: Dict[str, Any] = {}
        self.solver_fallbacks = 0
        self.stop_requested = False

class PilotEngine:
    def __init__(self):
        self.pilots: Dict[str, PilotContext] = {}

    async def start_pilot(self, req: PilotStartRequest):
        if req.pilot_id in self.pilots:
            if self.pilots[req.pilot_id].status == "running":
                return # Already running
        
        ctx = PilotContext(req)
        self.pilots[req.pilot_id] = ctx
        
        # Start background loop
        asyncio.create_task(self._pilot_loop(ctx))
        return ctx

    async def _pilot_loop(self, ctx: PilotContext):
        scenario = manager.get_scenario(ctx.scenario_id)
        if not scenario:
            ctx.status = "error"
            return

        current_state = scenario.initial_state.copy()
        
        # Simulation step interval (e.g., 1 min simulated time = 1 sec wall clock for demo)
        # We simulate 'horizon_minutes' steps
        for step in range(ctx.horizon_minutes):
            if ctx.stop_requested:
                break
            
            ctx.step_index = step
            
            # 1. Prepare data for optimizer (current state)
            ts_data = {
                "temperature": current_state.get("temperature"),
                "flow": current_state.get("flow"),
                "ts": time.time()
            }
            
            # 2. Get setpoints from optimizer
            batch_id = f"{ctx.pilot_id}-SIM-{step}"
            setpoints = await optimizer_client.recommend(batch_id, ts_data, mode=ctx.mode)
            
            # 3. Simulate step
            new_state = Simulator.simulate_step(current_state, setpoints, scenario, step, ctx.seed)
            
            # 4. Log results
            step_record = {
                "step": step,
                "timestamp": time.time(),
                "state": new_state,
                "setpoints": setpoints
            }
            ctx.timeseries.append(step_record)
            ctx.last_step_data = step_record
            
            # Compute KPI for this step
            step_kpi = Simulator.compute_kpis([new_state], scenario)
            ctx.kpis.append({"step": step, **step_kpi})
            
            current_state = new_state
            
            # Wall clock delay to simulate time passing (keep it short for testing)
            await asyncio.sleep(0.5) 

        ctx.status = "stopped"

    def get_health(self, pilot_id: str) -> Optional[PilotHealthResponse]:
        ctx = self.pilots.get(pilot_id)
        if not ctx:
            return None
        
        return PilotHealthResponse(
            pilot_id=ctx.pilot_id,
            uptime_sec=time.time() - ctx.start_time,
            progress=min(1.0, ctx.step_index / ctx.horizon_minutes) if ctx.horizon_minutes > 0 else 1.0,
            last_step=ctx.last_step_data
        )

    def get_snapshot(self, pilot_id: str) -> Optional[PilotSnapshotResponse]:
        ctx = self.pilots.get(pilot_id)
        if not ctx:
            return None
            
        # Summary metrics
        energy_mean = sum(k["energy_kwh"] for k in ctx.kpis) / len(ctx.kpis) if ctx.kpis else 0
        yield_mean = sum(k["yield_pct"] for k in ctx.kpis) / len(ctx.kpis) if ctx.kpis else 0
        quality_deviations = sum(1 for k in ctx.kpis if k.get("quality_deviation_count", 0) > 0)

        return PilotSnapshotResponse(
            pilot_id=ctx.pilot_id,
            scenario_id=ctx.scenario_id,
            mode=ctx.mode,
            timeseries=ctx.timeseries,
            kpis=ctx.kpis,
            summary={
                "energy_kwh_mean": round(energy_mean, 3),
                "yield_pct_mean": round(yield_mean, 2),
                "quality_deviations": quality_deviations,
                "solver_fallbacks": ctx.solver_fallbacks,
                "steps_completed": ctx.step_index
            }
        )

    def stop_pilot(self, pilot_id: str):
        ctx = self.pilots.get(pilot_id)
        if ctx:
            ctx.stop_requested = True
            ctx.status = "stopped"
            return True
        return False

pilot_engine = PilotEngine()
