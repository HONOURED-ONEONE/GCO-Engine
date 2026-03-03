import asyncio
import time
import uuid
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from app.api.services.twin import twin_service
from app.api.services.optimizer import recommend_setpoints
from app.api.services.kpi import ingest_kpi_service

class PilotService:
    def __init__(self):
        self.active_pilot = None
        self.running = False
        self.history = []
        self.stats = {
            "uptime_sec": 0,
            "reco_p95_ms": 0,
            "constraint_violations": 0,
            "cache_hit_ratio": 0.8, # Mock
            "batches_done": 0
        }
        self.start_time = None
        self.task = None

    async def start_pilot(self, pilot_id, twin_session_id, schedule, mode, canary_batches=3):
        if self.running:
            return {"error": "Pilot already running"}
            
        if not twin_service.running or twin_service.active_session != twin_session_id:
            return {"error": f"Twin session {twin_session_id} not running"}
            
        self.active_pilot = pilot_id
        self.running = True
        self.start_time = time.time()
        self.stats["batches_done"] = 0
        self.stats["reco_p95_ms"] = 0
        self.stats["constraint_violations"] = 0
        
        # Start orchestration task
        self.task = asyncio.create_task(self.orchestration_loop(mode, canary_batches))
        
        return {"pilot_id": pilot_id, "status": "running"}

    async def orchestration_loop(self, mode, canary_batches):
        plant = twin_service.plant
        batch_id = plant.start_batch()
        
        while self.running and twin_service.running:
            # 1. Read sensors
            status = plant.get_status()
            
            # 2. Get recommendation
            start_reco = time.time()
            # Call top-level function with live_state
            reco, err = recommend_setpoints(
                batch_id=status["batch_id"],
                live_state={
                    "temperature": status["temperature"],
                    "flow": status["flow"]
                }
            )
            reco_ms = (time.time() - start_reco) * 1000
            
            if reco is None:
                print(f"Optimizer Error: {err}")
                await asyncio.sleep(1)
                continue
                
            # Update stats
            self.stats["reco_p95_ms"] = 0.95 * self.stats["reco_p95_ms"] + 0.05 * reco_ms
            
            # 3. Apply SHADOW (log only, no real write-back)
            # In DT we'll apply it anyway for simulation if we are in shadow mode driving the DT
            step_res = plant.step(reco["setpoints"]["temperature"], reco["setpoints"]["flow"])
            
            # 4. Check guardrails
            if not reco.get("within_bounds", True):
                 self.stats["constraint_violations"] += 1
            
            # Log
            log_entry = {
                "ts": time.time(),
                "pilot_id": self.active_pilot,
                "batch_id": status["batch_id"],
                "step": status["step"],
                "mode": mode,
                "temperature": status["temperature"],
                "flow": status["flow"],
                "u_heat_shadow": reco["setpoints"]["temperature"],
                "u_valve_shadow": reco["setpoints"]["flow"],
                "compute_ms": reco_ms,
                "within_bounds": reco.get("within_bounds", True)
            }
            self.history.append(log_entry)
            
            # End of batch check
            if step_res["phase"] == "IDLE":
                self.stats["batches_done"] += 1
                
                # Ingest KPI using top-level function
                ingest_kpi_service(
                    batch_id=status["batch_id"],
                    energy_kwh=step_res["energy_kwh"],
                    yield_pct=step_res.get("yield_pct", 90.0), # Mock yield
                    quality_deviation=step_res["quality_violations"] > 0
                )
                
                # Start new batch
                batch_id = plant.start_batch()
            
            await asyncio.sleep(0.01) # Faster than real-time for testing

    async def stop_pilot(self):
        self.running = False
        if self.task:
            self.task.cancel()
        return {"pilot_id": self.active_pilot, "status": "stopped", "summary": self.get_health()}

    def get_health(self):
        if self.start_time:
            self.stats["uptime_sec"] = int(time.time() - self.start_time)
        return self.stats

    def get_snapshot(self):
        return {
            "pilot_id": self.active_pilot,
            "health": self.get_health(),
            "history_tail": self.history[-100:] if self.history else []
        }

pilot_service = PilotService()
